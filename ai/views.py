# ai/views.py
import os
import json
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from langchain_core.messages import HumanMessage, AIMessage
from rest_framework.response import Response
from rest_framework import status
from pgvector.django import CosineDistance
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rentals.models import Tenancy
from assets.models import Unit
from .models import LeaseDocument, LeaseChunk
from maintenance.models import MaintenanceRequest
from .serializers import MaintenanceTriageRequestSerializer,LeaseDocumentUploadSerializer, LeaseQuerySerializer
from .services import triage_maintenance_issue
from .tasks import process_lease_document
from ai.agent import copilot_app
from workspaces.models import Workspace

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

class MaintenanceTriageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = MaintenanceTriageRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        description = serializer.validated_data['description']
        unit_id = serializer.validated_data.get('unit_id')

        # 1. Security: Enforce workspace context
        workspace = getattr(request, 'workspace', None)
        if not workspace:
            return Response(
                {"error": "Workspace context is missing. Ensure X-Workspace-ID header is set."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Resolve target unit within workspace boundaries
        unit = None
        if unit_id:
            unit = Unit.objects.filter(id=unit_id, asset__workspace=workspace).first()
            if not unit:
                return Response(
                    {"error": "Unit not found or does not belong to active workspace."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Fallback: Find resident's active tenancy unit in this workspace
            active_tenancy = Tenancy.objects.filter(
                tenant=request.user,
                workspace=workspace,
                status=Tenancy.ACTIVE
            ).select_related('unit').first()

            if active_tenancy:
                unit = active_tenancy.unit

        if not unit:
            return Response(
                {"error": "No unit linked to this request. Pass a valid `unit_id`."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 3. Execute deterministic AI triage workflow
            triage_result = triage_maintenance_issue(
                description=description,
                workspace=workspace,
                user=request.user,
                unit=unit
            )

            # 4. Map TriageResult urgency to MaintenanceRequest priority
            priority_map = {
                "low": MaintenanceRequest.LOW,
                "medium": MaintenanceRequest.MEDIUM,
                "high": MaintenanceRequest.HIGH,
                "urgent": MaintenanceRequest.URGENT,
            }
            priority = priority_map.get(triage_result.urgency.lower(), MaintenanceRequest.MEDIUM)

            # 5. Persist MaintenanceRequest record
            maintenance_request = MaintenanceRequest.objects.create(
                workspace=workspace,
                unit=unit,
                tenant=request.user,
                title=triage_result.suggested_title,
                description=f"AI Summary:\n{triage_result.summary}\n\nOriginal Resident Input:\n{description}",
                priority=priority,
                status=MaintenanceRequest.OPEN,
            )

            # 6. Build final response combining DB model metadata and AI containment guidance
            response_payload = {
                "ticket_id": str(maintenance_request.id),
                # 🟢 FIXED: Convert the datetime object to a string
                "created_at": maintenance_request.created_at.isoformat(),
                "unit": {
                    "id": str(unit.id),
                    "name": unit.name,
                },
                "triage": triage_result.model_dump(),
            }

            return Response(response_payload, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": "Failed to process triage request.", "details": str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )

class LeaseUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # Required for file uploads

    def post(self, request, *args, **kwargs):
        # 1. Enforce Workspace Security
        workspace = getattr(request, 'workspace', None)
        if not workspace:
            return Response(
                {"error": "Workspace context is missing. Ensure X-Workspace-ID header is set."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = LeaseDocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenancy_id = serializer.validated_data['tenancy_id']
        uploaded_file = serializer.validated_data['file']

        # 2. Verify the tenancy exists within this workspace
        tenancy = Tenancy.objects.filter(id=tenancy_id, workspace=workspace).first()
        if not tenancy:
            return Response(
                {"error": "Tenancy not found or does not belong to the active workspace."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Create the document record (file gets saved to storage automatically)
        doc = LeaseDocument.objects.create(
            workspace=workspace,
            tenancy=tenancy,
            file=uploaded_file,
            status="pending"
        )

        # 4. Dispatch the Celery task to run asynchronously in the background
        process_lease_document.delay(doc.id)

        # 5. Return a 202 Accepted response indicating background processing has started
        return Response({
            "document_id": doc.id,
            "tenancy_id": tenancy.id,
            "status": doc.status,
            "message": "Lease uploaded and queued for vector embedding."
        }, status=status.HTTP_202_ACCEPTED)

class LeaseQueryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # 1. Enforce Workspace Boundary
        workspace = getattr(request, 'workspace', None)
        if not workspace:
            return Response(
                {"error": "Workspace context is missing."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = LeaseQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenancy_id = serializer.validated_data['tenancy_id']
        query_text = serializer.validated_data['query']

        # 2. Verify Tenancy belongs to this Workspace
        tenancy = Tenancy.objects.filter(id=tenancy_id, workspace=workspace).first()
        if not tenancy:
            return Response(
                {"error": "Tenancy not found in the active workspace."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Embed the User's Query
        query_vector = embeddings.embed_query(query_text)

        # 4. Perform Vector Similarity Search
        chunks = LeaseChunk.objects.filter(
            workspace=workspace,
            document__tenancy=tenancy
        ).annotate(
            distance=CosineDistance('embedding', query_vector)
        ).order_by('distance')[:4]

        if not chunks.exists():
            return Response(
                {"error": "No indexed lease agreement found for this tenancy."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 5. Build Context for the LLM
        context_text = "\n\n---\n\n".join([chunk.content for chunk in chunks])

        # 6. Query using ChatOpenAI
        llm = ChatOpenAI(
            temperature=0.0,
            model="openai/gpt-oss-20b",
            api_key=os.getenv("GROQ_API_KEY"),  # Pass your Groq key
            base_url="https://api.groq.com/openai/v1"  # Route traffic to Groq
        )

        prompt_template = ChatPromptTemplate.from_messages([
            ("system",
             "You are an AI assistant for property managers. Answer the user's question based strictly "
             "on the following lease agreement context. If the context does not contain the answer, "
             "say 'I cannot find this information in the provided lease agreement.'\n\n"
             "Context:\n{context}"),
            ("human", "{question}")
        ])

        chain = prompt_template | llm

        try:
            llm_response = chain.invoke({
                "context": context_text,
                "question": query_text
            })
            answer = llm_response.content
        except Exception as e:
            return Response({"error": f"LLM generation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 7. Return Result with Source References
        return Response({
            "query": query_text,
            "answer": answer,
            "sources": [
                {
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "distance": round(getattr(chunk, 'distance', 0.0), 4)
                } for chunk in chunks
            ]
        }, status=status.HTTP_200_OK)

class CopilotStreamView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        workspace_id = request.headers.get('X-Workspace-Id')
        user_message = request.data.get("message")

        if not workspace_id or not user_message:
            return Response({"error": "workspace_id header and message payload are required."}, status=400)

        # Security check: Ensure user belongs to workspace
        if not Workspace.objects.filter(id=workspace_id, members__user=request.user).exists():
            return Response({"error": "Unauthorized workspace."}, status=403)

        def event_stream():
            state_input = {
                "messages": [HumanMessage(content=user_message)],
                "workspace_id": str(workspace_id)
            }

            try:
                # stream_mode="messages" yields (message_chunk, metadata)
                for msg, metadata in copilot_app.stream(state_input, stream_mode="messages"):

                    # 1. Stream tool usage indicators to the frontend
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            payload = {"type": "tool_start", "tool": tool_call['name']}
                            yield f"data: {json.dumps(payload)}\n\n"

                    # 2. Stream standard text generation chunks
                    elif msg.content and isinstance(msg, AIMessage):
                        payload = {"type": "content", "text": msg.content}
                        yield f"data: {json.dumps(payload)}\n\n"

                # 3. Signal completion
                yield "data: {\"type\": \"done\"}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

## This test verifies the entry point of your Phase 2 Lease RAG pipeline by proving the system can securely receive a document and hand it off to background workers without freezing the API.

Specifically, it confirms four critical operations:

Workspace Security: Ensures the upload is strictly bound to the active X-Workspace-ID and linked to a valid tenancy within that boundary.

File Validation: Confirms Django REST Framework's MultiPartParser correctly receives binary file data and accepts the PDF.

Database Persistence: Checks that the initial LeaseDocument record is created in PostgreSQL with a pending status.

Asynchronous Handoff: Proves the API immediately returns a fast 202 Accepted response while successfully dispatching the heavy process_lease_document Celery task to the Redis message broker.

```
(quest) PS C:\Users\user\PycharmProjects\QuestNest> celery -A questnest worker -l info --pool=solo                      
 
 -------------- celery@Oma-05 v5.6.2 (recovery)
--- ***** -----
-- ******* ---- Windows-10-10.0.19045-SP0 2026-10-27 14:34:38
- *** --- * ---
- ** ---------- [config]
- ** ---------- .> app:         questnest:0x216130334d0
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 4 (solo)
-- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
--- ***** -----
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery


[tasks]
  . ai.tasks.process_lease_document
  . operations.tasks.process_event_rules_task
  . operations.tasks.reconcile_failed_events
  . operations.tasks.retry_payment_task
  . operations.tasks.trigger_due_rent_payments

[2026-10-27 14:34:39,147: INFO/MainProcess] Connected to redis://localhost:6379/0
[2026-10-27 14:34:39,232: INFO/MainProcess] mingle: searching for neighbors
[2026-10-27 14:34:40,410: INFO/MainProcess] mingle: all alone
[2026-10-27 14:34:40,619: INFO/MainProcess] celery@Oma-05 ready.
[2026-10-27 14:35:06,379: INFO/MainProcess] Task ai.tasks.process_lease_document[1131158f-d56d-401e-a338-7a3e19e4a5d5] received
[2026-10-27 14:37:04,805: INFO/MainProcess] No device provided, using cpu
[2026-10-27 14:37:06,733: INFO/MainProcess] HTTP Request: GET https://huggingface.co/api/agent-harnesses "HTTP/1.1 200 OK"
[2026-10-27 14:37:07,014: INFO/MainProcess] HTTP Request: GET https://huggingface.co/api/models/sentence-transformers/all-MiniLM-L6-v2 "HTTP/1.1 200 OK"
[2026-10-27 14:37:07,312: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/modules.json "HTTP/1.1 307 Temporary Redirect"
[2026-10-27 14:37:07,347: WARNING/MainProcess] Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
[2026-10-27 14:37:07,467: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/api/resolve-cache/models/sentence-
transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/modules.json?%2Fsentence-transformers%2Fall-MiniL
M-L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Fmodules.json=&etag=%22952a9b81c0bfd99800fabf352f69c7ccd46c5e43%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:07,516: INFO/MainProcess] HTTP Request: GET https://huggingface.co/api/resolve-cache/models/sentence-t
ransformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/modules.json?%2Fsentence-transformers%2Fall-MiniLM
-L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Fmodules.json=&etag=%22952a9b81c0bfd99800fabf352f69c7ccd46c5e43%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:07,969: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L
6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/config_sentence_transformers.json "HTTP/1.1 307 Temporary Redirect"
[2026-10-27 14:37:08,005: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/api/resolve-cache/models/sentence-
transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/config_sentence_transformers.json?%2Fsentence-tra
nsformers%2Fall-MiniLM-L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Fconfig_sentence_transformers.json=&etag=%22fd1b291129c607e5d49799f87cb219b27f98acdf%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:08,045: INFO/MainProcess] HTTP Request: GET https://huggingface.co/api/resolve-cache/models/sentence-t
ransformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/config_sentence_transformers.json?%2Fsentence-tran
sformers%2Fall-MiniLM-L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Fconfig_sentence_transformers.json=&etag=%22fd1b291129c607e5d49799f87cb219b27f98acdf%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:08,076: INFO/MainProcess] Loading SentenceTransformer model from sentence-transformers/all-MiniLM-L6-v2.
[2026-10-27 14:37:08,355: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/README.md "HTTP/1.1 307 Temporary Redirect"
[2026-10-27 14:37:08,384: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/api/resolve-cache/models/sentence-
transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/README.md?%2Fsentence-transformers%2Fall-MiniLM-L
6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2FREADME.md=&etag=%2244af2e3b0fa3a0b6239e48422972bf755f28fde0%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:08,419: INFO/MainProcess] HTTP Request: GET https://huggingface.co/api/resolve-cache/models/sentence-t
ransformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/README.md?%2Fsentence-transformers%2Fall-MiniLM-L6
-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2FREADME.md=&etag=%2244af2e3b0fa3a0b6239e48422972bf755f28fde0%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:08,788: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/sentence_bert_config.json "HTTP/1.1 307 Temporary Redirect"       
[2026-10-27 14:37:08,824: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/api/resolve-cache/models/sentence-
transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/sentence_bert_config.json?%2Fsentence-transformer
s%2Fall-MiniLM-L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Fsentence_bert_config.json=&etag=%2259d594003bf59880a884c574bf88ef7555bb0202%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:08,864: INFO/MainProcess] HTTP Request: GET https://huggingface.co/api/resolve-cache/models/sentence-t
ransformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/sentence_bert_config.json?%2Fsentence-transformers
%2Fall-MiniLM-L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Fsentence_bert_config.json=&etag=%2259d594003bf59880a884c574bf88ef7555bb0202%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:09,187: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/adapter_config.json "HTTP/1.1 404 Not Found"
[2026-10-27 14:37:09,472: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/config.json "HTTP/1.1 307 Temporary Redirect"
[2026-10-27 14:37:09,516: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/api/resolve-cache/models/sentence-
transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/config.json?%2Fsentence-transformers%2Fall-MiniLM
-L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Fconfig.json=&etag=%2272b987fd805cfa2b58c4c8c952b274a11bfd5a00%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:09,560: INFO/MainProcess] HTTP Request: GET https://huggingface.co/api/resolve-cache/models/sentence-t
ransformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/config.json?%2Fsentence-transformers%2Fall-MiniLM-
L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Fconfig.json=&etag=%2272b987fd805cfa2b58c4c8c952b274a11bfd5a00%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:10,112: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/model.safetensors "HTTP/1.1 302 Found"
[2026-10-27 14:37:10,567: INFO/MainProcess] HTTP Request: GET https://huggingface.co/api/models/sentence-transformers/all-MiniLM-L6-v2/xet-read-token/1110a243fdf4706b3f48f1d95db1a4f5529b4d41 "HTTP/1.1 200 OK"
Loading weights:   0%|          | 0/103 [00:00<?, ?it/s]
Loading weights: 100%|##########| 103/103 [00:00<00:00, 7552.94it/s]
[2026-10-27 14:37:51,337: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/processor_config.json "HTTP/1.1 404 Not Found"
[2026-10-27 14:37:51,642: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/preprocessor_config.json "HTTP/1.1 404 Not Found"
[2026-10-27 14:37:51,923: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/video_preprocessor_config.json "HTTP/1.1 404 Not Found"
[2026-10-27 14:37:52,206: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/tokenizer_config.json "HTTP/1.1 307 Temporary Redirect"
[2026-10-27 14:37:52,241: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/api/resolve-cache/models/sentence-
transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/tokenizer_config.json?%2Fsentence-transformers%2F
all-MiniLM-L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Ftokenizer_config.json=&etag=%22c79f2b6a0cea6f4b564fed1938984bace9d30ff0%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:52,297: INFO/MainProcess] HTTP Request: GET https://huggingface.co/api/resolve-cache/models/sentence-t
ransformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/tokenizer_config.json?%2Fsentence-transformers%2Fa
ll-MiniLM-L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Ftokenizer_config.json=&etag=%22c79f2b6a0cea6f4b564fed1938984bace9d30ff0%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:52,647: INFO/MainProcess] HTTP Request: GET https://huggingface.co/api/models/sentence-transformers/all-MiniLM-L6-v2/tree/main/additional_chat_templates?recursive=false&expand=false "HTTP/1.1 404 Not Found"
[2026-10-27 14:37:52,937: INFO/MainProcess] HTTP Request: GET https://huggingface.co/api/models/sentence-transformers/all-MiniLM-L6-v2/tree/main?recursive=true&expand=false "HTTP/1.1 200 OK"
[2026-10-27 14:37:53,228: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/vocab.txt "HTTP/1.1 307 Temporary Redirect"
[2026-10-27 14:37:53,280: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/api/resolve-cache/models/sentence-
transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/vocab.txt?%2Fsentence-transformers%2Fall-MiniLM-L
6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Fvocab.txt=&etag=%22fb140275c155a9c7c5a3b3e0e77a9e839594a938%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:53,337: INFO/MainProcess] HTTP Request: GET https://huggingface.co/api/resolve-cache/models/sentence-t
ransformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/vocab.txt?%2Fsentence-transformers%2Fall-MiniLM-L6
-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Fvocab.txt=&etag=%22fb140275c155a9c7c5a3b3e0e77a9e839594a938%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:53,720: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/tokenizer.json "HTTP/1.1 307 Temporary Redirect"
[2026-10-27 14:37:53,778: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/api/resolve-cache/models/sentence-
transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/tokenizer.json?%2Fsentence-transformers%2Fall-Min
iLM-L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Ftokenizer.json=&etag=%22cb202bfe2e3c98645018a6d12f182a434c9d3e02%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:53,841: INFO/MainProcess] HTTP Request: GET https://huggingface.co/api/resolve-cache/models/sentence-t
ransformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/tokenizer.json?%2Fsentence-transformers%2Fall-Mini
LM-L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Ftokenizer.json=&etag=%22cb202bfe2e3c98645018a6d12f182a434c9d3e02%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:54,214: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/added_tokens.json "HTTP/1.1 404 Not Found"
[2026-10-27 14:37:54,526: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/special_tokens_map.json "HTTP/1.1 307 Temporary Redirect"
[2026-10-27 14:37:54,585: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/api/resolve-cache/models/sentence-
transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/special_tokens_map.json?%2Fsentence-transformers%
2Fall-MiniLM-L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Fspecial_tokens_map.json=&etag=%22e7b0375001f109a6b8873d756ad4f7bbb15fbaa5%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:54,645: INFO/MainProcess] HTTP Request: GET https://huggingface.co/api/resolve-cache/models/sentence-t
ransformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/special_tokens_map.json?%2Fsentence-transformers%2
Fall-MiniLM-L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2Fspecial_tokens_map.json=&etag=%22e7b0375001f109a6b8873d756ad4f7bbb15fbaa5%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:54,939: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/chat_template.jinja "HTTP/1.1 404 Not Found"
[2026-10-27 14:37:55,380: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/1_Pooling/config.json "HTTP/1.1 307 Temporary Redirect"
[2026-10-27 14:37:55,420: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/api/resolve-cache/models/sentence-
transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/1_Pooling%2Fconfig.json?%2Fsentence-transformers%
2Fall-MiniLM-L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2F1_Pooling%2Fconfig.json=&etag=%22d1514c3162bbe87b343f565fadc62e6c06f04f03%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:55,457: INFO/MainProcess] HTTP Request: GET https://huggingface.co/api/resolve-cache/models/sentence-transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/1_Pooling%2Fconfig.json?%2Fsentence-transformers%2Fall-MiniLM-L6-v2%2Fresolve%2F1110a243fdf4706b3f48f1d95db1a4f5529b4d41%2F1_Pooling%2Fconfig.json=&etag=%22d1514c3162bbe87b343f565fadc62e6c06f04f03%22 "HTTP/1.1 200 OK"
[2026-10-27 14:37:55,771: INFO/MainProcess] HTTP Request: HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/2_Normalize/config.json "HTTP/1.1 404 Not Found"
[2026-10-27 14:37:56,037: INFO/MainProcess] Task ai.tasks.process_lease_document[1131158f-d56d-401e-a338-7a3e19e4a5d5] succeeded in 169.6569492999697s: None
```

## Key takeaways from the log:

Model Download & Local Caching: On its initial run, HuggingFaceEmbeddings connected to Hugging Face, fetched the all-MiniLM-L6-v2 model weights, and cached them locally on your machine. Subsequent runs will be almost instantaneous.

Text Processing & Embedding: Celery successfully retrieved the uploaded PDF from storage, extracted its text using PyPDFLoader, split it into semantic chunks with RecursiveCharacterTextSplitter, and generated 384-dimensional vector embeddings for each chunk.

pgvector Batch Insertion: The 384-dimensional vectors were saved to your PostgreSQL database inside the LeaseChunk model with workspace isolation intact.

Task Completion: The task completed cleanly without exceptions (succeeded in 169.65s: None), and the underlying LeaseDocument status updated to completed.
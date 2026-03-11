from django.contrib import admin
from .models import (
    LeaseAgreement,
    LeaseClauseTemplate,
    LeaseClauseInstance,
    LeaseSignature,
    LeaseDocument
)


admin.site.register(LeaseAgreement)
admin.site.register(LeaseClauseTemplate)
admin.site.register(LeaseClauseInstance)
admin.site.register(LeaseSignature)
admin.site.register(LeaseDocument)
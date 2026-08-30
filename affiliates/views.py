import hashlib
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.db.models import F
from .models import AffiliateLink, ClickLog


class AffiliateRedirectView(View):
    def get(self, request, pk):
        # 1. Busca o link de afiliado e garante que está ativo e com a plataforma ativa
        link = get_object_or_404(
            AffiliateLink, 
            pk=pk, 
            active=True, 
            platform__active=True
        )

        # 2. Incremento atômico para o campo `clicks` do seu model
        AffiliateLink.objects.filter(pk=pk).update(clicks=F('clicks') + 1)

        # 3. Pega o IP e aplica Hash (SHA-256) em conformidade com a LGPD
        raw_ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if raw_ip:
            raw_ip = raw_ip.split(',')[0].strip()
        else:
            raw_ip = request.META.get('REMOTE_ADDR', '')

        ip_hash = hashlib.sha256(raw_ip.encode('utf-8')).hexdigest() if raw_ip else ''

        # 4. Captura do User-Agent e do Referrer (Source)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        source = request.META.get('HTTP_REFERER', '')[:255]

        # 5. Salva o ClickLog
        ClickLog.objects.create(
            link=link,
            ip_hash=ip_hash,
            user_agent=user_agent,
            source=source
        )

        # 6. Redireciona o usuário para a URL de afiliado
        return redirect(link.affiliate_url)
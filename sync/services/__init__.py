from sync.services.amazon import AmazonSyncService
from sync.services.mercado_livre import MercadoLivreSyncService
from sync.services.shopee import ShopeeSyncService

SERVICES = {
    "mercado_livre": MercadoLivreSyncService,
    "shopee": ShopeeSyncService,
    "amazon": AmazonSyncService,
}


def get_sync_service(platform_code: str):
    service_cls = SERVICES.get(platform_code)
    if not service_cls:
        raise ValueError(
            f"Nenhum serviço de sync configurado para a plataforma '{platform_code}'"
        )
    return service_cls()
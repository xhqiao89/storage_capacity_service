from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.stores import PersistentStore


class StorageCapacityService(TethysAppBase):
    """
    Tethys app class for ls.
    """

    name = 'Storage Capacity Service'
    index = 'storage_capacity_service:home'
    icon = 'storage_capacity_service/images/icon.gif'
    package = 'storage_capacity_service'
    root_url = 'storage-capacity-service'
    color = '#e67e22'
        
    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (UrlMap(name='home',
                            url='storage-capacity-service',
                            controller='storage_capacity_service.controllers.home'),
                    UrlMap(name='run',
                           url='storage-capacity-service/run',
                           controller='storage_capacity_service.controllers.run_sc'),
                    UrlMap(name='get',
                           url='storage-capacity-service/get',
                           controller='storage_capacity_service.controllers.get_sc'),
                    UrlMap(name='stop',
                           url='storage-capacity-service/stop',
                           controller='storage_capacity_service.controllers.stop_sc'),
                    UrlMap(name='download',
                           url='storage-capacity-service/download',
                           controller='storage_capacity_service.controllers.download_output_files'),

        )

        return url_maps

    def persistent_stores(self):
        """
        Add one or more persistent stores
        """
        stores = (PersistentStore(name='storage_capacity_service_db',
                                  initializer='init_stores:init_storage_capacity_service_db',
                                  spatial=True
                ),
        )

        return stores
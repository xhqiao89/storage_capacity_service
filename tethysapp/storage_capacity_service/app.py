from tethys_sdk.base import TethysAppBase, url_map_maker


class Ls(TethysAppBase):
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
                    UrlMap(name='download',
                           url='storage-capacity-service/download',
                           controller='storage_capacity_service.controllers.download_output_files'),

        )

        return url_maps
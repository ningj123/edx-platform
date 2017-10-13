"""
This command will be run by an ansible script.
"""

import logging

from provider.oauth2.models import Client
from provider.constants import CONFIDENTIAL
from edx_oauth2_provider.models import TrustedClient
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.theming.models import SiteTheme
from .sites_configuration import get_sites_data

LOG = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command to create the site, site themes, configuration and oauth2 clients for all WL-sites.

    Example:
    ./manage.py lms create_sites_and_configurations --dns-name whitelabel
    """
    dns_name = None
    ecommerce_user = None
    discovery_user = None

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            "--dns-name",
            type=str,
            help="Enter DNS name of sandbox.",
            required=True
        )

    def _create_oauth2_client(self, url, site_name, is_discovery=True):
        """
        Creates the oauth2 client and add it in trusted clients.
        """

        client, _ = Client.objects.get_or_create(
            redirect_uri="{url}complete/edx-oidc/".format(url=url),
            defaults={
                "user": self.discovery_user if is_discovery else self.ecommerce_user,
                "name": "{site_name}_{client_type}_client".format(
                    site_name=site_name,
                    client_type="discovery" if is_discovery else "ecommerce",
                ),
                "url": url,
                "client_id": "{client_type}-key-{site_name}".format(
                    client_type="discovery" if is_discovery else "ecommerce",
                    site_name=site_name
                ),
                "client_secret": "{client_type}-secret-{dns_name}".format(
                    client_type="discovery" if is_discovery else "ecommerce",
                    dns_name=self.dns_name
                ),
                "client_type": CONFIDENTIAL,
                "logout_uri": "{url}logout/".format(url=url)
            }
        )
        LOG.info("Adding {client} oauth2 client as trusted client".format(client=client.name))
        TrustedClient.objects.get_or_create(client=client)

    def _create_sites(self, site_domain, theme_dir_name, site_configuration):
        """
        Create Sites, SiteThemes and SiteConfigurations
        """
        site, created = Site.objects.get_or_create(
            domain=site_domain,
            defaults={"name": site_domain}
        )
        if created:
            LOG.info("Creating '{site_name}' SiteTheme".format(site_name=site_domain))
            SiteTheme.objects.create(site=site, theme_dir_name=theme_dir_name)

            LOG.info("Creating '{site_name}' SiteConfiguration".format(site_name=site_domain))
            SiteConfiguration.objects.create(site=site, values=site_configuration, enabled=True)
        else:
            LOG.info(" '{site_domain}' site already exists".format(site_domain=site_domain))

    def _generate_urls(self, site_name):
        """
        Generate the lms, discovery and ecommerce URLs for a site.
        """
        lms_url = "{site_name}-{dns_name}.sandbox.edx.org".format(site_name=site_name, dns_name=self.dns_name)
        discovery_url = "https://discovery-{site_name}-{dns_name}.edx.org/".format(
            site_name=site_name,
            dns_name=self.dns_name
        )
        ecommerce_url = "https://ecommerce-{site_name}-{dns_name}.edx.org/".format(
            site_name=site_name,
            dns_name=self.dns_name
        )
        if site_name == "edx":
            lms_url = "{dns_name}.sandbox.edx.org".format(dns_name=self.dns_name)
            discovery_url = "https://discovery-{dns_name}.edx.org/".format(
                dns_name=self.dns_name
            )
            ecommerce_url = "https://ecommerce-{dns_name}.edx.org/".format(
                dns_name=self.dns_name
            )
        return lms_url, discovery_url, ecommerce_url

    def get_or_create_service_user(self, username):
        """
        Creates the service user for ecommerce and discovery.
        """
        return User.objects.get_or_create(
            username=username,
            defaults={
                "is_staff": True,
                "is_superuser": True
            }
        )

    def handle(self, *args, **options):

        self.dns_name = options['dns_name']

        self.discovery_user, _ = self.get_or_create_service_user("lms_catalog_service_user")
        self.ecommerce_user, _ = self.get_or_create_service_user("ecommerce_worker")

        all_sites = get_sites_data(self.dns_name)

        # creating Sites, SiteThemes, SiteConfigurations and oauth2 clients
        for site_name, site_data in all_sites.items():

            site_domain, discovery_url, ecommerce_url = self._generate_urls(site_name)

            LOG.info("Creating '{site_name}' Site".format(site_name=site_name))
            self._create_sites(site_domain, site_data['theme_dir_name'], site_data['configuration'])

            LOG.info("Creating discovery oauth2 client for '{site_name}' site".format(site_name=site_name))
            self._create_oauth2_client(discovery_url, site_name, is_discovery=True)

            LOG.info("Creating ecommerce oauth2 client for '{site_name}' site".format(site_name=site_name))
            self._create_oauth2_client(ecommerce_url, site_name, is_discovery=False)

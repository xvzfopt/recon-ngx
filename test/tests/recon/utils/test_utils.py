# =====================================================================================
# Imports: External
# =====================================================================================

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.utils import utils
from test.abs_testcase import AbsTestCase

# =====================================================================================
# Utils Test Case Class
# =====================================================================================
class TestUtils(AbsTestCase):
    '''
    BaseModule Test Case
    '''

    # =====================================================================================
    # General Methods
    # =====================================================================================

    # =====================================================================================
    # Test Methods
    # =====================================================================================
    def test_hosts_to_domains(self):
        '''
        Tests domain_to_hosts --> extraction of domain names list from a list of hosts
        '''

        # Test 1 - (No exclusions)
        hosts = ["hello.test.apis.google.com", "my.test.domain.name.org"]
        expected_domains = [
            "test.apis.google.com", "apis.google.com", "google.com",
            "test.domain.name.org", "domain.name.org", "name.org"
        ]
        domains = utils.hosts_to_domains(hosts)
        self.assertEqual(domains, expected_domains)

        # Test 2 (Some Exclusions)
        expected_domains.remove("domain.name.org")
        domains = utils.hosts_to_domains(hosts, ["domain.name.org"])
        self.assertEqual(domains, expected_domains)

    def test_cidr_to_list(self):
        '''
        Tests cidr_to_list --> Expansion of a CIDR string to a list of IP Addresses
        '''

        # Test 1 - /24 Network
        cidr = "192.168.0.0/24"
        ips = utils.cidr_to_list(cidr)

        self.assertLength(256, ips)
        for octet in range(0, 256):
            self.assertIn("192.168.0.%s" % octet, ips)

        # Test 2 - /32 Network
        cidr = "192.168.5.59/32"
        ips = utils.cidr_to_list(cidr)
        self.assertEqual(["192.168.5.59"], ips)

    def test_html_escape(self):
        '''
        Tests html_escape --> Escaping special characters within HTML content
        '''
        content = "This is a < > test & ' \""
        expected = "This is a &lt; &gt; test &amp; &apos; &quot;"
        new_content = utils.html_escape(content)
        self.assertEqual(expected, new_content)

    def test_html_unescape(self):
        '''
        Tests html_unescape --> Unescaping special characters within HTML content
        '''
        content = "This is a &lt; &gt; test &amp; &apos; &quot;"
        expected = "This is a < > test & ' \""
        new_content = utils.html_unescape(content)
        self.assertEqual(expected, new_content)

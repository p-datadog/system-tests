from utils import context, BaseTestCase, interfaces


class Test_Telemetry(BaseTestCase):
    """Test that instrumentation telemetry is sent"""

    def test_status_ok(self):
        """Test that telemetry requests are successful"""
        interfaces.library.assert_telemetry_requests_are_successful()
        interfaces.agent.assert_telemetry_requests_are_successful()

    def test_seq_id(self):
        """Test that messages are sent sequentially"""
        interfaces.library.assert_seq_ids_are_roughly_sequential()
        interfaces.library.assert_no_skipped_seq_ids()

    def test_app_started(self):
        """Request type app-started is sent on startup"""
        interfaces.library.assert_send_app_started()

    def test_integrations_change(self):
        """Request type integrations-change have non empty list of changes"""
        interfaces.library.assert_integrations_changed_message_valid()

    def test_proxy_forwarding(self):
        """Test that the telemetry proxy forwards messages correctly"""
        interfaces.library.assert_all_telemetry_messages_proxied(interfaces.agent)

import pytest
from playwright.sync_api import expect

@pytest.mark.ui
def test_request_helper_logic(ui_page):
    """Test the request helper logic in static/app.js."""
    # Check if request method exists
    exists = ui_page.evaluate("() => typeof Alpine.$data(document.querySelector('[x-data]')).request === 'function'")
    assert exists, "Request method should exist"

    # Test path normalization and URL construction
    ui_page.evaluate("""
        const component = Alpine.$data(document.querySelector('[x-data]'));
        component.remoteApiUrl = 'http://remote-api.com/';
        component.apiKey = 'test-key';
        
        // Mock fetch
        window._fetchCalls = [];
        window.fetch = async (url, options) => {
            window._fetchCalls.push({url, options});
            return {
                status: 200,
                ok: true,
                json: async () => ({})
            };
        };
    """)

    # Clear any calls that might have happened during setup
    ui_page.evaluate("() => window._fetchCalls = []")

    ui_page.evaluate("() => Alpine.$data(document.querySelector('[x-data]')).request('api/test')")
    
    fetch_calls = ui_page.evaluate("() => window._fetchCalls")
    assert len(fetch_calls) >= 1
    # Check the last call
    last_call = fetch_calls[-1]
    assert last_call['url'] == 'http://remote-api.com/api/test'
    assert last_call['options']['headers']['X-API-Key'] == 'test-key'

@pytest.mark.ui
def test_request_helper_headers(ui_page):
    """Test that the request helper adds headers correctly."""
    # This will be used after I implement the method.
    pass

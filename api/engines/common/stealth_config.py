"""
Stealth Configuration for Anti-Bot Detection Bypass
Comprehensive stealth measures for browser automation.
"""

import random
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


# =============================================================================
# USER AGENT POOL - Realistic, up-to-date user agents
# =============================================================================

USER_AGENTS = {
    "chrome_windows": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ],
    "chrome_mac": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    ],
    "edge_windows": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    ],
    "firefox_windows": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    ],
}

# Thai-focused user agents (for Shopee Thailand)
USER_AGENTS_THAI = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]


# =============================================================================
# VIEWPORT CONFIGURATIONS
# =============================================================================

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
]


# =============================================================================
# SCREEN CONFIGURATIONS
# =============================================================================

SCREENS = [
    {"width": 1920, "height": 1080, "deviceScaleFactor": 1},
    {"width": 2560, "height": 1440, "deviceScaleFactor": 1},
    {"width": 1366, "height": 768, "deviceScaleFactor": 1},
    {"width": 1536, "height": 864, "deviceScaleFactor": 1.25},
]


# =============================================================================
# LOCALES AND TIMEZONES
# =============================================================================

LOCALES = ["th-TH", "th", "en-US", "en"]
TIMEZONES = ["Asia/Bangkok", "Asia/Bangkok"]  # Thailand timezone


# =============================================================================
# STEALTH JAVASCRIPT INJECTIONS
# =============================================================================

STEALTH_SCRIPTS = {
    # Hide webdriver property
    "webdriver": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """,
    
    # Override plugins with realistic values
    "plugins": """
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const plugins = [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
                ];
                plugins.length = 3;
                return plugins;
            }
        });
    """,
    
    # Override languages
    "languages": """
        Object.defineProperty(navigator, 'languages', {
            get: () => ['th-TH', 'th', 'en-US', 'en']
        });
    """,
    
    # Override platform
    "platform": """
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32'
        });
    """,
    
    # Override hardwareConcurrency (realistic values)
    "hardwareConcurrency": """
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });
    """,
    
    # Override deviceMemory
    "deviceMemory": """
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });
    """,
    
    # Hide automation indicators
    "automation": """
        // Remove automation-related properties
        delete navigator.__proto__.webdriver;
        
        // Override permissions query
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """,
    
    # WebGL fingerprint randomization
    "webgl": """
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.call(this, parameter);
        };
    """,
    
    # Canvas fingerprint protection
    "canvas": """
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            if (this.width === 220 && this.height === 30) {
                // Likely a fingerprint attempt, add noise
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] ^= (Math.random() * 2) | 0;
                    }
                    context.putImageData(imageData, 0, 0);
                }
            }
            return originalToDataURL.apply(this, arguments);
        };
    """,
    
    # Audio fingerprint protection
    "audio": """
        const audioContext = window.AudioContext || window.webkitAudioContext;
        if (audioContext) {
            const originalCreateAnalyser = audioContext.prototype.createAnalyser;
            audioContext.prototype.createAnalyser = function() {
                const analyser = originalCreateAnalyser.call(this);
                const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                analyser.getFloatFrequencyData = function(array) {
                    originalGetFloatFrequencyData.call(this, array);
                    array[0] += Math.random() * 0.0001;
                };
                return analyser;
            };
        }
    """,
    
    # Override iframe contentWindow
    "iframe": """
        Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
            get: function() {
                return window;
            }
        });
    """,
    
    # Override connection info
    "connection": """
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                rtt: 50,
                downlink: 10,
                saveData: false
            })
        });
    """,
    
    # Chrome runtime check
    "chrome_runtime": """
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
    """,
    
    # Permission API
    "permissions": """
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """,
    
    # Screen info
    "screen": """
        Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
        Object.defineProperty(screen, 'pixelDepth', { get: () => 24 });
    """,
    
    # Timezone spoofing
    "timezone": """
        const originalDateTimeFormat = Intl.DateTimeFormat;
        Intl.DateTimeFormat = function(locale, options) {
            if (options && options.timeZone) {
                options.timeZone = 'Asia/Bangkok';
            }
            return new originalDateTimeFormat(locale, options);
        };
    """,
}

# Combined stealth script
FULL_STEALTH_SCRIPT = "\n".join(STEALTH_SCRIPTS.values())


# =============================================================================
# REQUEST HEADERS
# =============================================================================

def get_realistic_headers(user_agent: str = None) -> Dict[str, str]:
    """
    Generate realistic HTTP headers for requests.
    
    Args:
        user_agent: User agent string (will use random if not provided)
    
    Returns:
        Dictionary of headers
    """
    ua = user_agent or random.choice(USER_AGENTS_THAI)
    
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": ua,
    }


def get_shopee_headers(user_agent: str = None, referer: str = None) -> Dict[str, str]:
    """
    Generate headers specifically for Shopee requests.
    
    Args:
        user_agent: User agent string
        referer: Referer URL
    
    Returns:
        Dictionary of headers
    """
    headers = get_realistic_headers(user_agent)
    
    # Shopee-specific headers
    headers.update({
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://shopee.co.th",
        "Referer": referer or "https://shopee.co.th/",
        "X-Requested-With": "XMLHttpRequest",
        "X-Shopee-Language": "th",
    })
    
    return headers


# =============================================================================
# PROXY CONFIGURATION
# =============================================================================

@dataclass
class ProxyConfig:
    """Proxy configuration for request rotation."""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"  # http, https, socks5
    
    @property
    def url(self) -> str:
        """Get proxy URL."""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def playwright_proxy(self) -> Dict[str, str]:
        """Get Playwright-compatible proxy config."""
        return {
            "server": f"{self.protocol}://{self.host}:{self.port}",
            "username": self.username,
            "password": self.password,
        }


# =============================================================================
# BROWSER FINGERPRINT
# =============================================================================

@dataclass
class BrowserFingerprint:
    """Complete browser fingerprint configuration."""
    user_agent: str = field(default_factory=lambda: random.choice(USER_AGENTS_THAI))
    viewport: Dict[str, int] = field(default_factory=lambda: random.choice(VIEWPORTS))
    screen: Dict[str, Any] = field(default_factory=lambda: random.choice(SCREENS))
    locale: str = "th-TH"
    timezone: str = "Asia/Bangkok"
    color_depth: int = 24
    device_memory: int = 8
    hardware_concurrency: int = 8
    
    @classmethod
    def random(cls) -> "BrowserFingerprint":
        """Generate a random but consistent fingerprint."""
        return cls(
            user_agent=random.choice(USER_AGENTS_THAI),
            viewport=random.choice(VIEWPORTS),
            screen=random.choice(SCREENS),
        )
    
    def get_context_args(self) -> Dict[str, Any]:
        """Get Playwright context arguments."""
        return {
            "user_agent": self.user_agent,
            "viewport": self.viewport,
            "screen": self.screen,
            "locale": self.locale,
            "timezone_id": self.timezone,
            "color_scheme": "light",
            "has_touch": False,
            "is_mobile": False,
            "java_script_enabled": True,
        }


# =============================================================================
# HUMAN BEHAVIOR SIMULATION
# =============================================================================

def get_random_delay(min_ms: int = 100, max_ms: int = 500) -> float:
    """
    Get a random delay in seconds with human-like distribution.
    
    Args:
        min_ms: Minimum delay in milliseconds
        max_ms: Maximum delay in milliseconds
    
    Returns:
        Delay in seconds
    """
    # Use exponential distribution for more natural delays
    delay_ms = random.uniform(min_ms, max_ms)
    # Add occasional longer pauses (simulating reading/thinking)
    if random.random() < 0.1:  # 10% chance
        delay_ms += random.uniform(500, 2000)
    return delay_ms / 1000.0


def get_typing_delay() -> float:
    """Get realistic typing delay between keystrokes."""
    # Average typing speed: 40-60 WPM = 200-300ms per character
    base_delay = random.uniform(0.05, 0.15)
    # Occasional pauses
    if random.random() < 0.05:
        base_delay += random.uniform(0.3, 0.8)
    return base_delay


def get_scroll_distance() -> int:
    """Get realistic scroll distance."""
    # Most scrolls are small (reading), some are larger (skipping)
    if random.random() < 0.7:
        return random.randint(100, 400)  # Small scroll
    else:
        return random.randint(400, 1000)  # Larger scroll


def get_mouse_movement_steps(distance: int) -> int:
    """Get number of steps for mouse movement (more steps = smoother)."""
    # Roughly 10-20 pixels per step
    return max(5, distance // random.randint(10, 20))


# =============================================================================
# ANTI-BOT DETECTION BYPASS STRATEGIES
# =============================================================================

class StealthStrategy:
    """Strategy for bypassing different types of anti-bot detection."""
    
    @staticmethod
    def get_init_script() -> str:
        """Get the full stealth initialization script."""
        return FULL_STEALTH_SCRIPT
    
    @staticmethod
    def get_browser_args() -> List[str]:
        """Get Chrome arguments for stealth mode."""
        return [
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-site-isolation-trials",
            "--disable-web-security",
            "--disable-features=BlockInsecurePrivateNetworkRequests",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-infobars",
            "--disable-background-networking",
            "--disable-breakpad",
            "--disable-component-update",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-sync",
            "--metrics-recording-only",
            "--no-first-run",
            "--disable-hang-monitor",
            "--disable-prompt-on-repost",
            "--disable-client-side-phishing-detection",
            "--disable-component-extensions-with-background-pages",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-translate",
            "--disable-plugins",
            "--disable-plugins-discovery",
            "--disable-prerender-local-predictor",
            "--disable-session-crashed-bubble",
            "--disable-setuid-sandbox",
            "--disable-signin-promo",
            "--disable-speech-api",
            "--disable-translate-new-ux",
            "--disable-voice-input",
            "--disable-wake-on-wifi",
            "--enable-async-dns",
            "--enable-simple-cache-backend",
            "--enable-tcp-fast-open",
            "--enable-webgl",
            "--ignore-certificate-errors",
            "--ignore-gpu-blacklist",
            "--media-cache-size=1048576",
            "--disk-cache-size=1048576",
            "--window-position=0,0",
        ]
    
    @staticmethod
    def get_experimental_options() -> Dict[str, Any]:
        """Get Chrome experimental options."""
        return {
            "excludeSwitches": [
                "enable-automation",
                "enable-logging",
                "enable-blink-features",
            ],
            "useAutomationExtension": False,
            "prefs": {
                "credentials_enable_service": False,
                "credentials_enable_manager": False,
                "profile.password_manager_enabled": False,
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_setting_values.geolocation": 2,
                "profile.default_content_setting_values.media_stream": 2,
                "profile.default_content_setting_values.popups": 2,
                "profile.default_content_setting_values.plugins": 2,
                "profile.default_content_setting_values.automatic_downloads": 2,
                "profile.default_content_setting_values.midi_sysex": 2,
                "profile.default_content_setting_values.push_messaging": 2,
                "profile.default_content_setting_values.ssl_cert_decisions": 2,
                "profile.default_content_setting_values.durable_storage": 2,
                "profile.block_third_party_cookies": False,
                "intl.accept_languages": "th-TH,th,en-US,en",
            }
        }


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

@dataclass
class SessionConfig:
    """Session configuration for maintaining state."""
    session_id: str = field(default_factory=lambda: hashlib.md5(str(random.random()).encode()).hexdigest()[:12])
    cookies_file: Optional[str] = None
    storage_file: Optional[str] = None
    user_agent: str = field(default_factory=lambda: random.choice(USER_AGENTS_THAI))
    created_at: float = field(default_factory=lambda: random.random())
    
    def get_storage_path(self, base_dir: str) -> str:
        """Get storage path for this session."""
        return f"{base_dir}/sessions/{self.session_id}"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data for logging."""
    if len(data) <= visible_chars:
        return "*" * len(data)
    return data[:visible_chars] + "*" * (len(data) - visible_chars)


def is_likely_bot_detection_page(html_content: str) -> bool:
    """Check if page content indicates bot detection."""
    indicators = [
        "captcha",
        "verify you are human",
        "access denied",
        "blocked",
        "rate limit",
        "too many requests",
        "security check",
        "cf-browser-verification",
        "challenge-platform",
        "ray id:",
        "incident id:",
    ]
    
    content_lower = html_content.lower()
    return any(indicator in content_lower for indicator in indicators)


def get_retry_delay(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """
    Calculate exponential backoff delay with jitter.
    
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    
    Returns:
        Delay in seconds
    """
    # Exponential backoff with jitter
    delay = min(base_delay * (2 ** attempt), max_delay)
    # Add jitter (±25%)
    jitter = delay * random.uniform(-0.25, 0.25)
    return max(0, delay + jitter)

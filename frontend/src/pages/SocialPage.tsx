// pages/SocialPage.tsx — Social Hub: Quick access to social platforms
import React from 'react';
import '../styles/social-hub.css';

interface Platform {
  name: string;
  icon: string;
  url: string;
  color: string;
}

const platforms: Platform[] = [
  { name: 'Facebook', icon: '📘', url: 'https://www.facebook.com/', color: '#3b82f6' },
  { name: 'TikTok', icon: '🎵', url: 'https://www.tiktok.com/', color: '#ff0050' },
  { name: 'Shopee', icon: '🛒', url: 'https://shopee.co.th/', color: '#f97316' },
  { name: 'Line', icon: '💬', url: 'https://line.me/', color: '#00b900' },
  { name: 'Instagram', icon: '📸', url: 'https://www.instagram.com/', color: '#e1306c' },
  { name: 'YouTube', icon: '▶️', url: 'https://www.youtube.com/', color: '#ff0000' },
];

const SocialPage: React.FC = () => {
  const lastSynced = new Date().toLocaleTimeString();

  const handleCardClick = (url: string) => {
    window.open(url, '_blank');
  };

  return (
    <div className="sh-tabs-container">
      <main className="sh-main">
        <header className="sh-main-header">
          <div className="sh-main-title">
            <span className="sh-page-title">🌐 SOCIAL HUB</span>
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            Last synced: {lastSynced}
          </div>
        </header>

        <div className="sh-platform-grid">
          {platforms.map((platform) => (
            <div
              key={platform.name}
              className="sh-platform-card"
              style={{ '--card-color': platform.color } as React.CSSProperties}
              onClick={() => handleCardClick(platform.url)}
            >
              <div className="sh-card-dot" />
              <span className="sh-card-icon">{platform.icon}</span>
              <span className="sh-card-name">{platform.name}</span>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default SocialPage;

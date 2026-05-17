// pages/FacebookConnectPage.tsx — Facebook OAuth and Post Interface
import React, { useState, useEffect } from 'react';
import '../styles/facebook.css';
import { useAppStore } from '../stores/useAppStore';

interface Page {
  id: string;
  name: string;
  access_token?: string;
}

interface Post {
  id: string;
  message: string;
  created_time: string;
  permalink_url: string;
  full_picture?: string;
}

const FacebookConnectPage: React.FC = () => {
  const [connected, setConnected] = useState(false);
  const [oauthUrl, setOauthUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [pages, setPages] = useState<Page[]>([]);
  const [selectedPage, setSelectedPage] = useState<Page | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [postMessage, setPostMessage] = useState('');
  const [postLink, setPostLink] = useState('');
  const [posting, setPosting] = useState(false);
  const [postResult, setPostResult] = useState<{ success?: boolean; error?: string } | null>(null);

  // Fetch connection status on mount
  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/facebook/status');
      const data = await res.json();
      setConnected(data.connected);
      
      if (data.connected) {
        fetchPages();
        fetchPosts();
      } else {
        fetchOauthUrl();
      }
    } catch (e) {
      console.error('Failed to fetch Facebook status:', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchOauthUrl = async () => {
    try {
      const res = await fetch('/api/facebook/oauth/url');
      const data = await res.json();
      setOauthUrl(data.url);
    } catch (e) {
      console.error('Failed to fetch OAuth URL:', e);
    }
  };

  const fetchPages = async () => {
    try {
      const res = await fetch('/api/facebook/pages');
      const data = await res.json();
      if (data.pages) {
        setPages(data.pages);
        if (data.pages.length > 0) {
          setSelectedPage(data.pages[0]);
        }
      }
    } catch (e) {
      console.error('Failed to fetch pages:', e);
    }
  };

  const fetchPosts = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/facebook/posts', { headers: { 'Authorization': `Bearer ${token}` } });
      const data = await res.json();
      if (data.posts) {
        setPosts(data.posts);
      }
    } catch (e) {
      console.error('Failed to fetch posts:', e);
    }
  };

  const handleConnect = () => {
    if (oauthUrl) {
      // Open OAuth popup
      window.open(oauthUrl, 'facebook_oauth', 'width=600,height=700');
    }
  };

  const handleDisconnect = async () => {
    try {
      const token = localStorage.getItem('token');
      await fetch('/api/facebook/disconnect', { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } });
      setConnected(false);
      setPages([]);
      setSelectedPage(null);
      setPosts([]);
    } catch (e) {
      console.error('Failed to disconnect:', e);
    }
  };

  const handlePost = async () => {
    if (!postMessage.trim() && !postLink.trim()) return;
    
    setPosting(true);
    setPostResult(null);
    
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/facebook/post', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: postMessage,
          link: postLink || undefined,
        }),
      });
      const data = await res.json();
      
      if (data.success) {
        setPostResult({ success: true });
        setPostMessage('');
        setPostLink('');
        fetchPosts(); // Refresh posts
      } else {
        setPostResult({ error: data.error });
      }
    } catch (e) {
      setPostResult({ error: 'Failed to create post' });
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="scroll fb-page">
      <div className="fb-header">
        <div className="fb-title">
          <span className="fb-icon">📘</span>
          <h2>Facebook Connect</h2>
        </div>
        <p className="fb-subtitle">Manage your Facebook pages and posts</p>
      </div>

      {loading ? (
        <div className="fb-loading">
          <div className="fb-spinner" />
          <p>Loading...</p>
        </div>
      ) : (
        <>
          {/* Connection Status Card */}
          <div className="fb-card fb-status-card">
            <div className="fb-status-header">
              <h3>Connection Status</h3>
              <span className={`fb-badge ${connected ? 'connected' : 'disconnected'}`}>
                {connected ? '✓ Connected' : '✗ Not Connected'}
              </span>
            </div>
            
            {!connected ? (
              <div className="fb-connect-section">
                <p>Connect your Facebook account to manage pages and create posts.</p>
                <button className="fb-btn fb-btn-primary" onClick={handleConnect}>
                  🔗 Connect Facebook
                </button>
              </div>
            ) : (
              <div className="fb-connected-section">
                <p>Your Facebook account is connected.</p>
                <button className="fb-btn fb-btn-danger" onClick={handleDisconnect}>
                  Disconnect
                </button>
              </div>
            )}
          </div>

          {/* Pages Selection */}
          {connected && (
            <div className="fb-card fb-pages-card">
              <h3>Select Page</h3>
              {pages.length === 0 ? (
                <p className="fb-empty">No pages found. Make sure your Facebook account has pages.</p>
              ) : (
                <div className="fb-pages-list">
                  {pages.map(page => (
                    <div
                      key={page.id}
                      className={`fb-page-item ${selectedPage?.id === page.id ? 'selected' : ''}`}
                      onClick={() => setSelectedPage(page)}
                    >
                      <span className="fb-page-icon">📄</span>
                      <span className="fb-page-name">{page.name}</span>
                      {selectedPage?.id === page.id && <span className="fb-check">✓</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Post Creator */}
          {connected && selectedPage && (
            <div className="fb-card fb-post-card">
              <h3>Create Post</h3>
              <p className="fb-post-page-info">Posting to: <strong>{selectedPage.name}</strong></p>
              
              <div className="fb-post-form">
                <textarea
                  className="fb-textarea"
                  placeholder="What's on your mind?"
                  value={postMessage}
                  onChange={e => setPostMessage(e.target.value)}
                  rows={4}
                />
                
                <input
                  type="url"
                  className="fb-input"
                  placeholder="Link (optional)"
                  value={postLink}
                  onChange={e => setPostLink(e.target.value)}
                />
                
                {postResult && (
                  <div className={`fb-result ${postResult.success ? 'success' : 'error'}`}>
                    {postResult.success ? '✓ Post published successfully!' : `✗ ${postResult.error}`}
                  </div>
                )}
                
                <button
                  className="fb-btn fb-btn-post"
                  onClick={handlePost}
                  disabled={posting || (!postMessage.trim() && !postLink.trim())}
                >
                  {posting ? 'Posting...' : '📘 Publish Post'}
                </button>
              </div>
            </div>
          )}

          {/* Recent Posts */}
          {connected && posts.length > 0 && (
            <div className="fb-card fb-posts-card">
              <h3>Recent Posts</h3>
              <div className="fb-posts-list">
                {posts.map(post => (
                  <div key={post.id} className="fb-post-item">
                    {post.full_picture && (
                      <img src={post.full_picture} alt="" className="fb-post-image" />
                    )}
                    <div className="fb-post-content">
                      <p className="fb-post-message">{post.message || '(No message)'}</p>
                      <div className="fb-post-meta">
                        <span>{new Date(post.created_time).toLocaleString()}</span>
                        {post.permalink_url && (
                          <a href={post.permalink_url} target="_blank" rel="noopener noreferrer">
                            View on Facebook ↗
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default FacebookConnectPage;

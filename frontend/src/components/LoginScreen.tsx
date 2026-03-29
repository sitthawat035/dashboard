// src/components/LoginScreen.tsx
import React from 'react';

interface LoginScreenProps {
  password: string;
  setPassword: (val: string) => void;
  onLogin: () => void;
  loginError: boolean;
}

const LoginScreen: React.FC<LoginScreenProps> = ({
  password,
  setPassword,
  onLogin,
  loginError,
}) => {
  return (
    <div id="login-overlay" className="glass animate-fade">
      <div className="login-box glass">
        <div className="login-icon">🎛️</div>
        <h2>Unified Authentication</h2>
        <p>Accessing JOEPV Master Hub v3.1</p>
        
        <div className="input-field">
            <input
                type="password" 
                placeholder="Enter bypass code..."
                value={password}
                onChange={e => setPassword(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && onLogin()}
                autoFocus
            />
            <button className="login-btn" onClick={onLogin}>➔</button>
        </div>
        
        {loginError && <div className="login-error animate-fade">Invalid access token provided.</div>}
        
        <div className="login-footer">
            <span>🛡️ SECURE SESSION</span>
            <span>v3.0.1</span>
        </div>
      </div>
    </div>
  );
};

export default LoginScreen;

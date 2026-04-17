// components/AgentCard/FileManager.tsx — File explorer + editor panel
import { useState, useEffect } from 'react';
import SimpleFileList from './SimpleFileList';
import { gatewayApi } from '../../utils/api';

interface FileManager {
  name: string;
  size: number;
  is_workspace?: boolean;
}

interface FileManagerProps {
  gw: string;
}

const FileManager: React.FC<FileManagerProps> = ({ gw }) => {
  const [files, setFiles] = useState<FileManager[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [fileContent, setFileContent] = useState<string>('');
  const [fileSaving, setFileSaving] = useState(false);
  const [fileLoading, setFileLoading] = useState(false);
  const [fileError, setFileError] = useState<string>('');
  const [fileMetadata, setFileMetadata] = useState<{ name: string; size: number; modified: string } | null>(null);
  const [expandedFolders, setExpandedFolders] = useState<Set<string> | null>(null);
  const [filesLoading, setFilesLoading] = useState(false);

  // Load files when component mounts
  useEffect(() => {
    setFilesLoading(true);
    gatewayApi.getFiles(gw)
      .then(({ ok, data: d }) => {
        if (ok && d) {
          setFiles(d.files || []);
          setExpandedFolders(new Set<string>());
        }
        setFilesLoading(false);
      })
      .catch(err => {
        console.error('Files API error:', err);
        setFilesLoading(false);
      });
  }, [gw]);

  const refreshFiles = () => {
    setFilesLoading(true);
    gatewayApi.getFiles(gw).then(({ ok, data: d }) => {
      if (ok && d) setFiles(d.files || []);
      setFilesLoading(false);
    }).catch(() => setFilesLoading(false));
  };

  const toggleFolder = (folder: string) => {
    setExpandedFolders(prev => {
      if (!prev) return new Set([folder]);
      const next = new Set(prev);
      if (next.has(folder)) {
        next.delete(folder);
      } else {
        next.add(folder);
      }
      return next;
    });
  };

  // Load file content when selection changes
  useEffect(() => {
    if (selectedFile) {
      setFileLoading(true);
      setFileError('');
      setFileContent('');
      setFileMetadata(null);
      gatewayApi.getFile(gw, selectedFile)
        .then(({ ok, data: d }) => {
          if (!ok || !d) {
            setFileError('Failed to load file');
            setFileContent('');
          } else if (d.error) {
            setFileError(d.error);
            setFileContent('');
          } else {
            setFileContent(d.content || '');
            setFileMetadata(d.metadata || null);
            setFileError('');
          }
        })
        .catch(e => {
          console.error('File fetch error:', e);
          setFileError(`Error loading file: ${e.message}`);
          setFileContent('');
        })
        .finally(() => setFileLoading(false));
    }
  }, [selectedFile, gw]);

  const saveFile = async () => {
    if (!selectedFile) return;
    setFileSaving(true);
    try {
      await gatewayApi.saveFile(gw, selectedFile, fileContent);
    } catch (e) { console.error(e); }
    setFileSaving(false);
  };

  return (
    <div className="config-wrapper">
      <div className="file-explorer">
        <div className="file-explorer-header">
          <span className="file-explorer-title">FILES</span>
          <button className="file-explorer-refresh" onClick={refreshFiles} disabled={filesLoading}>
            {filesLoading ? '⏳' : '🔄'} Refresh
          </button>
        </div>
        <div className="file-explorer-content">
          {filesLoading ? (
            <div className="file-explorer-empty">
              <div className="file-explorer-empty-icon">⏳</div>
              <div className="file-explorer-empty-text">Loading files...</div>
            </div>
          ) : files.length === 0 ? (
            <div className="file-explorer-empty">
              <div className="file-explorer-empty-icon">📂</div>
              <div className="file-explorer-empty-text">No files found</div>
            </div>
          ) : (
            <SimpleFileList
              files={files}
              selectedFile={selectedFile}
              onSelectFile={setSelectedFile}
              expandedFolders={expandedFolders ?? new Set<string>()}
              onToggleFolder={toggleFolder}
            />
          )}
        </div>
      </div>
      <div className="file-editor">
        {selectedFile ? (
          <>
            <div className="editor-header">
              <div className="editor-title-section">
                <span className="editor-tag">EDITING</span>
                <span className="editor-filename">{selectedFile}</span>
                {fileMetadata && (
                  <span className="editor-meta">
                    {(fileMetadata.size / 1024).toFixed(1)}K • {new Date(fileMetadata.modified).toLocaleString()}
                  </span>
                )}
              </div>
              <div className="editor-actions">
                <button className="btn-save" onClick={saveFile} disabled={fileSaving || fileLoading}>
                  {fileSaving ? '⌛ Saving...' : '💾 Save File'}
                </button>
              </div>
            </div>
            {fileLoading ? (
              <div className="editor-loading">
                <div className="loading-spinner">⏳</div>
                <p>Loading file...</p>
              </div>
            ) : fileError ? (
              <div className="editor-error">
                <div className="error-icon">⚠️</div>
                <p className="error-message">{fileError}</p>
              </div>
            ) : (
              <div className="editor-content">
                <textarea
                  className="editor-textarea"
                  value={fileContent}
                  onChange={e => setFileContent(e.target.value)}
                  spellCheck={false}
                  placeholder="File content..."
                />
              </div>
            )}
          </>
        ) : (
          <div className="editor-placeholder">
            <div className="placeholder-icon">📄</div>
            <p className="placeholder-text">Select a file from the explorer to view and edit</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileManager;

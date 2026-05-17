import React from 'react';

interface FileItem {
  name: string;
  size: number;
  is_workspace?: boolean;
}

interface FileExplorerTreeProps {
  files: FileItem[];
  selectedFile: string;
  onSelectFile: (name: string) => void;
  expandedFolders: Set<string>;
  onToggleFolder: (folder: string) => void;
}

interface FolderNode {
  files: FileItem[];
  subfolders: Record<string, FolderNode>;
}

const buildFolderTree = (files: FileItem[]) => {
  const folders: Record<string, FolderNode> = {};
  const rootFiles: FileItem[] = [];

  files.forEach(f => {
    const parts = f.name.split(/[/\\]/);
    if (parts.length > 1) {
      const rootFolder = parts[0];
      if (!folders[rootFolder]) {
        folders[rootFolder] = { files: [], subfolders: {} };
      }

      if (parts.length === 2) {
        folders[rootFolder].files.push(f);
      } else {
        let current = folders[rootFolder].subfolders;
        for (let i = 1; i < parts.length - 1; i++) {
          const part = parts[i];
          if (!current[part]) {
            current[part] = { files: [], subfolders: {} };
          }
          current = current[part].subfolders;
        }
        current[parts[parts.length - 2]].files.push(f);
      }
    } else {
      rootFiles.push(f);
    }
  });

  return { folders, rootFiles };
};

const renderSubfolders = (
  subfolders: Record<string, FolderNode>,
  parentPath: string,
  depth: number,
  selectedFile: string,
  onSelectFile: (name: string) => void,
  expandedFolders: Set<string>,
  onToggleFolder: (folder: string) => void
) => {
  return Object.keys(subfolders).sort().map(subfolder => {
    const folderPath = `${parentPath}/${subfolder}`;
    const isExpanded = expandedFolders.has(folderPath);

    return (
      <div key={folderPath} className="explorer-folder">
        <div
          className="explorer-folder-header"
          onClick={() => onToggleFolder(folderPath)}
          style={{ paddingLeft: `${8 + depth * 12}px` }}
        >
          <span className={`explorer-folder-icon ${isExpanded ? 'expanded' : ''}`}>▶</span>
          <span className="explorer-folder-name">{subfolder}</span>
          <span className={`explorer-folder-expand-icon ${isExpanded ? 'expanded' : ''}`}>
            {isExpanded ? '▼' : '▶'}
          </span>
        </div>
        {isExpanded && (
          <div className="explorer-folder-children">
            {subfolders[subfolder].files.map(f => (
              <div
                key={f.name}
                className={`explorer-file ${selectedFile === f.name ? 'active' : ''}`}
                onClick={() => onSelectFile(f.name)}
                style={{ paddingLeft: `${16 + depth * 12}px` }}
              >
                <span className="explorer-file-icon">📄</span>
                <span className="explorer-file-name">{f.name.split(/[/\\]/).pop()}</span>
                <span className="explorer-file-size">{(f.size / 1024).toFixed(1)}K</span>
                {f.is_workspace && <span className="explorer-workspace-badge">WS</span>}
              </div>
            ))}
            {renderSubfolders(
              subfolders[subfolder].subfolders,
              folderPath,
              depth + 1,
              selectedFile,
              onSelectFile,
              expandedFolders,
              onToggleFolder
            )}
          </div>
        )}
      </div>
    );
  });
};

const FileExplorerTree: React.FC<FileExplorerTreeProps> = ({
  files,
  selectedFile,
  onSelectFile,
  expandedFolders,
  onToggleFolder,
}) => {
  const { folders, rootFiles } = buildFolderTree(files);

  return (
    <>
      {Object.keys(folders).sort().map(rootFolder => {
        const isExpanded = expandedFolders.has(rootFolder);

        return (
          <div key={rootFolder} className="explorer-folder">
            <div className="explorer-folder-header" onClick={() => onToggleFolder(rootFolder)}>
              <span className={`explorer-folder-icon ${isExpanded ? 'expanded' : ''}`}>▶</span>
              <span className="explorer-folder-name">{rootFolder}</span>
              <span className={`explorer-folder-expand-icon ${isExpanded ? 'expanded' : ''}`}>
                {isExpanded ? '▼' : '▶'}
              </span>
            </div>
            {isExpanded && (
              <div className="explorer-folder-children">
                {folders[rootFolder].files.map(f => (
                  <div
                    key={f.name}
                    className={`explorer-file ${selectedFile === f.name ? 'active' : ''}`}
                    onClick={() => onSelectFile(f.name)}
                  >
                    <span className="explorer-file-icon">📄</span>
                    <span className="explorer-file-name">{f.name.split(/[/\\]/).pop()}</span>
                    <span className="explorer-file-size">{(f.size / 1024).toFixed(1)}K</span>
                    {f.is_workspace && <span className="explorer-workspace-badge">WS</span>}
                  </div>
                ))}
                {renderSubfolders(
                  folders[rootFolder].subfolders,
                  rootFolder,
                  1,
                  selectedFile,
                  onSelectFile,
                  expandedFolders,
                  onToggleFolder
                )}
              </div>
            )}
          </div>
        );
      })}
      {rootFiles.map(f => (
        <div
          key={f.name}
          className={`explorer-file ${selectedFile === f.name ? 'active' : ''}`}
          onClick={() => onSelectFile(f.name)}
        >
          <span className="explorer-file-icon">📄</span>
          <span className="explorer-file-name">{f.name}</span>
          <span className="explorer-file-size">{(f.size / 1024).toFixed(1)}K</span>
          {f.is_workspace && <span className="explorer-workspace-badge">WS</span>}
        </div>
      ))}
    </>
  );
};

export default FileExplorerTree;
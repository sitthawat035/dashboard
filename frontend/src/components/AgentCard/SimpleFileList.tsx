import React from 'react';

interface FileItem {
  name: string;
  size: number;
  is_workspace?: boolean;
}

interface NestedFolderProps {
  folders: Record<string, any>;
  prefix: string;
  expandedFolders: Set<string>;
  onToggleFolder: (folder: string) => void;
  selectedFile: string;
  onSelectFile: (name: string) => void;
  depth?: number;
}

const NestedFolder: React.FC<NestedFolderProps> = ({
  folders,
  prefix,
  expandedFolders,
  onToggleFolder,
  selectedFile,
  onSelectFile,
  depth = 0,
}) => {
  const keys = Object.keys(folders).sort();
  
  return (
    <>
      {keys.map(key => {
        const folderPath = prefix ? `${prefix}/${key}` : key;
        const isExpanded = expandedFolders.has(folderPath);
        const folder = folders[key];
        
        return (
          <div key={folderPath}>
            <div 
              className="file-group-header" 
              onClick={() => onToggleFolder(folderPath)}
              style={{ paddingLeft: `${depth * 16 + 8}px` }}
            >
              <span className="file-group-icon">{isExpanded ? '📂' : '📁'}</span>
              <span className="file-group-name">{key}</span>
              {folder.files && folder.files.length > 0 && (
                <span className="file-group-count">({folder.files.length})</span>
              )}
            </div>
            {isExpanded && (
              <div className="file-group-items">
                {folder.files?.map((f: FileItem) => (
                  <div
                    key={f.name}
                    className={`file-item-simple ${selectedFile === f.name ? 'active' : ''}`}
                    onClick={() => onSelectFile(f.name)}
                    style={{ paddingLeft: `${(depth + 1) * 16 + 8}px` }}
                  >
                    <span className="file-item-icon">📄</span>
                    <span className="file-item-name">{f.name.split('/').pop()}</span>
                    <span className="file-item-size">{(f.size / 1024).toFixed(1)}K</span>
                  </div>
                ))}
                {folder.subfolders && (
                  <NestedFolder
                    folders={folder.subfolders}
                    prefix={folderPath}
                    expandedFolders={expandedFolders}
                    onToggleFolder={onToggleFolder}
                    selectedFile={selectedFile}
                    onSelectFile={onSelectFile}
                    depth={depth + 1}
                  />
                )}
              </div>
            )}
          </div>
        );
      })}
    </>
  );
};

interface SimpleFileListProps {
  files: FileItem[];
  selectedFile: string;
  onSelectFile: (name: string) => void;
  expandedFolders: Set<string>;
  onToggleFolder: (folder: string) => void;
}

const SimpleFileList: React.FC<SimpleFileListProps> = ({
  files,
  selectedFile,
  onSelectFile,
  expandedFolders,
  onToggleFolder,
}) => {
  const buildTree = () => {
    const tree: Record<string, any> = { files: [], subfolders: {} };
    
    files.forEach(f => {
      const parts = f.name.split('/');
      if (parts.length === 1) {
        // Top-level file
        tree.files.push(f);
      } else {
        // File is in a subfolder
        let current = tree;
        
        // Navigate/create folders for all parts EXCEPT the filename (last part)
        for (let i = 0; i < parts.length - 1; i++) {
          const part = parts[i];
          if (!current.subfolders[part]) {
            current.subfolders[part] = { files: [], subfolders: {} };
          }
          current = current.subfolders[part];
        }
        
        // Now add file to the parent folder's files array
        current.files.push(f);
      }
    });
    
    return tree;
  };
  
  const tree = buildTree();
  
  return (
    <div className="file-list-simple">
      <NestedFolder
        folders={tree.subfolders}
        prefix=""
        expandedFolders={expandedFolders}
        onToggleFolder={onToggleFolder}
        selectedFile={selectedFile}
        onSelectFile={onSelectFile}
        depth={0}
      />
      {tree.files.map((f: FileItem) => (
        <div
          key={f.name}
          className={`file-item-simple ${selectedFile === f.name ? 'active' : ''}`}
          onClick={() => onSelectFile(f.name)}
        >
          <span className="file-item-icon">📄</span>
          <span className="file-item-name">{f.name}</span>
          <span className="file-item-size">{(f.size / 1024).toFixed(1)}K</span>
        </div>
      ))}
    </div>
  );
};

export default SimpleFileList;
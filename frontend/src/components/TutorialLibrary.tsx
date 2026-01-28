import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Tutorial {
  id: string;
  goal: string;
  original_instruction: string;
  success_criteria: string;
  steps_count: number;
  video_url: string;
  video_filename: string;
  download_url: string;
  file_size_mb: number;
  created_at: string;
}

interface Props {
  onSelectTutorial?: (tutorial: Tutorial) => void;
}

const API_URL = process.env.REACT_APP_SERVER_API_URL;

const TutorialLibrary: React.FC<Props> = ({ onSelectTutorial }) => {
  const [tutorials, setTutorials] = useState<Tutorial[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [playingId, setPlayingId] = useState<string | null>(null);

  useEffect(() => {
    fetchTutorials();
  }, []);

  const fetchTutorials = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/api/tutorials`);
      setTutorials(response.data.tutorials);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load tutorials');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!window.confirm('Are you sure you want to delete this tutorial?')) {
      return;
    }

    try {
      await axios.delete(`${API_URL}/api/tutorials/${id}`);
      setTutorials(tutorials.filter(t => t.id !== id));
      if (expandedId === id) setExpandedId(null);
      if (playingId === id) setPlayingId(null);
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to delete tutorial');
    }
  };

  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const toggleExpand = (id: string) => {
    if (expandedId === id) {
      setExpandedId(null);
      setPlayingId(null);
    } else {
      setExpandedId(id);
    }
  };

  const togglePlay = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setPlayingId(playingId === id ? null : id);
  };

  if (loading) {
    return (
      <div className="tutorial-library">
        <h2>Tutorial Library</h2>
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading tutorials...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="tutorial-library">
        <h2>Tutorial Library</h2>
        <div className="error-state">
          <p>Error: {error}</p>
          <button className="btn btn-secondary" onClick={fetchTutorials}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (tutorials.length === 0) {
    return (
      <div className="tutorial-library">
        <h2>Tutorial Library</h2>
        <div className="empty-state">
          <div className="empty-icon">🎬</div>
          <h3>No tutorials yet</h3>
          <p>Create your first video tutorial by entering an instruction above.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="tutorial-library">
      <div className="library-header">
        <h2>Tutorial Library</h2>
        <span className="tutorial-count">{tutorials.length} tutorial{tutorials.length !== 1 ? 's' : ''}</span>
        <button className="btn-icon refresh-btn" onClick={fetchTutorials} title="Refresh">
          🔄
        </button>
      </div>

      <div className="tutorials-grid">
        {tutorials.map((tutorial) => (
          <div 
            key={tutorial.id} 
            className={`tutorial-card ${expandedId === tutorial.id ? 'expanded' : ''}`}
          >
            <div className="tutorial-header" onClick={() => toggleExpand(tutorial.id)}>
              <div className="tutorial-info">
                <h3 className="tutorial-title">{tutorial.goal}</h3>
                <div className="tutorial-meta">
                  <span className="meta-item">
                    📅 {formatDate(tutorial.created_at)}
                  </span>
                  <span className="meta-item">
                    📊 {tutorial.steps_count} steps
                  </span>
                  <span className="meta-item">
                    💾 {tutorial.file_size_mb} MB
                  </span>
                </div>
              </div>
              <div className="tutorial-actions">
                <button 
                  className="btn-icon play-btn"
                  onClick={(e) => togglePlay(tutorial.id, e)}
                  title={playingId === tutorial.id ? "Close" : "Play"}
                >
                  {playingId === tutorial.id ? '⏹️' : '▶️'}
                </button>
                <a 
                  href={`${API_URL}${tutorial.download_url}`}
                  className="btn-icon download-btn"
                  onClick={(e) => e.stopPropagation()}
                  download={tutorial.video_filename}
                  title="Download"
                >
                  ⬇️
                </a>
                <button 
                  className="btn-icon delete-btn"
                  onClick={(e) => handleDelete(tutorial.id, e)}
                  title="Delete"
                >
                  🗑️
                </button>
              </div>
            </div>

            {/* Video Player - Shown when playing */}
            {playingId === tutorial.id && (
              <div className="tutorial-video">
                <video
                  controls
                  autoPlay
                  src={`${API_URL}${tutorial.video_url}`}
                >
                  Your browser does not support the video tag.
                </video>
              </div>
            )}

            {/* Expanded Details */}
            {expandedId === tutorial.id && playingId !== tutorial.id && (
              <div className="tutorial-details">
                {tutorial.original_instruction && (
                  <div className="detail-section">
                    <label>Original Instruction:</label>
                    <p>{tutorial.original_instruction}</p>
                  </div>
                )}
                {tutorial.success_criteria && (
                  <div className="detail-section">
                    <label>Success Criteria:</label>
                    <p>{tutorial.success_criteria}</p>
                  </div>
                )}
                <div className="detail-actions">
                  <button 
                    className="btn btn-primary"
                    onClick={(e) => togglePlay(tutorial.id, e)}
                  >
                    ▶️ Play Video
                  </button>
                  <a 
                    href={`${API_URL}${tutorial.download_url}`}
                    className="btn btn-secondary"
                    download={tutorial.video_filename}
                  >
                    ⬇️ Download
                  </a>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TutorialLibrary;
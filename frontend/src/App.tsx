import React, { useState, useEffect, useRef } from 'react';
import axios, { formToJSON } from 'axios';
import VideoRequestForm from './components/VideoRequestForm';
import TaskPlanEditor from './components/TaskPlanEditor';
import VideoPlayer from './components/VideoPlayer';
import StatusIndicator from './components/StatusIndicator';
import TutorialLibrary from './components/TutorialLibrary';
import { JobStatus, TaskPlan } from './types';
import './App.css';

const API_URL = process.env.REACT_APP_SERVER_API_URL + '/api';

function App() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showLibrary, setShowLibrary] = useState(true);
  
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // Polling for status
  useEffect(() => {
    if (jobId && jobStatus && ! ['completed', 'failed', 'plan_ready'].includes(jobStatus. status)) {
      pollingRef.current = setInterval(async () => {
        try {
          const response = await axios. get(`${API_URL}/status/${jobId}`);
          setJobStatus(response.data);
          
          if (['completed', 'failed', 'plan_ready'].includes(response.data.status)) {
            setIsLoading(false);
            if (pollingRef.current) {
              clearInterval(pollingRef.current);
            }
          }
        } catch (err) {
          console.error('Polling error:', err);
        }
      }, 2000);
      
      return () => {
        if (pollingRef. current) {
          clearInterval(pollingRef.current);
        }
      };
    }
  }, [jobId, jobStatus?. status]);

  const handleSubmitInstruction = async (instruction: string) => {
    setIsLoading(true);
    setError(null);
    setJobStatus(null);
    setJobId(null);
    setShowLibrary(false);
    
    try {
      const response = await axios.post(`${API_URL}/generate-plan`, {
        instruction
      });
      
      setJobId(response.data.job_id);
      setJobStatus({
        id: response.data. job_id,
        status:  'pending',
        message: 'Generating plan',
        instruction,
        task_plan: null,
        video_url: null,
        video_filename: null,
        results: null,
        error: null,
        created_at: new Date().toISOString()
      });
    } catch (err:  any) {
      setError(err.response?.data?.error || 'Error generating plan');
      setIsLoading(false);
    }
  };

  const handleSaveTaskPlan = async (plan: TaskPlan) => {
    if (!jobId) return;
    
    try {
      await axios.put(`${API_URL}/task-plan/${jobId}`, plan);
      setJobStatus(prev => prev ? { ...prev, task_plan: plan } : null);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error saving plan');
    }
  };

  const handleExecute = async () => {
    if (!jobId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      await axios.post(`${API_URL}/execute/${jobId}`);
      setJobStatus(prev => prev ? { 
        ...prev, 
        status: 'recording',
        message: 'Starting recording'
      } : null);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error executing');
      setIsLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!jobId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      await axios.post(`${API_URL}/regenerate/${jobId}`);
      setJobStatus(prev => prev ? { 
        ...prev, 
        status: 'recording',
        message: 'Regenerating video',
        video_url: null,
        video_filename: null
      } : null);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error regenerating');
      setIsLoading(false);
    }
  };

  const resetAll = () => {
    setJobId(null);
    setJobStatus(null);
    setError(null);
    setIsLoading(false);
    setShowLibrary(true);
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🎬 Video Tutorial Generator</h1>
        <p>Automatically create video tutorials</p>
        {jobId && (
          <button className="btn-reset" onClick={resetAll}>
            🔄 New Request
          </button>
        )}
      </header>

      <main className="main">
        {/* Input form that is shown only if there is no active job */}
        {! jobId && (
          <VideoRequestForm
            onSubmit={handleSubmitInstruction}
            isLoading={isLoading}
          />
        )}

        {/* Error */}
        {error && (
          <div className="error-banner">
            ❌ {error}
          </div>
        )}

        {/* Status */}
        {jobStatus && (
          <StatusIndicator
            status={jobStatus.status}
            message={jobStatus.message}
            error={jobStatus.error}
          />
        )}

        {/* Task Plan Editor that is shown when the plan is ready */}
        {jobStatus?.task_plan && jobStatus.status !== 'completed' && (
          <TaskPlanEditor
            taskPlan={jobStatus.task_plan}
            onSave={handleSaveTaskPlan}
            onExecute={handleExecute}
            isLoading={isLoading}
          />
        )}

        {/* Video Player that is shown when the video is ready */}
        {jobStatus?.status === 'completed' && jobStatus.video_url && (
          <>
            <VideoPlayer
              videoUrl={jobStatus.video_url}
              videoFilename={jobStatus.video_filename || ''}
              onRegenerate={handleRegenerate}
              isLoading={isLoading}
              results={jobStatus.results}
            />
            
            {/* Show plan below the video for possible edits */}
            {jobStatus.task_plan && (
              <TaskPlanEditor
                taskPlan={jobStatus.task_plan}
                onSave={handleSaveTaskPlan}
                onExecute={handleRegenerate}
                isLoading={isLoading}
              />
            )}
          </>
        )}
        {showLibrary && !jobId && (
          <TutorialLibrary />
        )}

        {/* Show library after completion too */}
        {jobStatus?.status === 'completed' && (
          <TutorialLibrary />
        )}
      </main>

      <footer className="footer">
        <p>Powered by Groq AI + OpenRouter Vision + FFmpeg</p>
      </footer>
    </div>
  );
}

export default App;
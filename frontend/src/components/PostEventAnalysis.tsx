import { useState } from "react";
import axios from "axios";
import { BarChart3, AlertTriangle, Star } from "lucide-react";

interface PostEventAnalysisProps {
  track?: string;
  race?: string;
}

interface AnalysisData {
  file_name?: string;
  track?: string;
  race?: string;
  data_analysis?: any;
  key_moments?: any[];
  ai_story?: any;
  race_summary?: any;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function PostEventAnalysis({ track, race }: PostEventAnalysisProps) {
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadTrack, setUploadTrack] = useState(track || "");
  const [uploadRace, setUploadRace] = useState(race || "");
  const [file, setFile] = useState<File | null>(null);

  const handleFileUpload = async () => {
    if (!file) {
      setError("Please select a file to upload");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      
      const params: any = {};
      if (uploadTrack) params.track = uploadTrack;
      if (uploadRace) params.race = uploadRace;

      const response = await axios.post(
        `${API_BASE_URL}/insights/post-event-analysis`,
        formData,
        {
          params,
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      setAnalysis(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to analyze file");
    } finally {
      setLoading(false);
    }
  };

  const loadExistingAnalysis = async () => {
    if (!track || !race) return;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(
        `${API_BASE_URL}/insights/post-event-analysis/${track}/${race}`
      );
      setAnalysis(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load analysis");
    } finally {
      setLoading(false);
    }
  };

  const aiStory = analysis?.ai_story || {};

  return (
    <div className="w-full space-y-6">
      <h3 className="text-xl font-bold text-primary flex items-center gap-2">
        <BarChart3 className="h-6 w-6 text-primary" /> Post-Event Analysis
      </h3>

      {/* Upload Section */}
      <div className="glass-card p-6">
        <h4 className="text-lg font-bold text-white mb-4">Upload Race Data</h4>
        <div className="flex flex-col md:flex-row gap-4 items-end">
          <div className="flex-1 w-full space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase">Track</label>
            <input
              type="text"
              value={uploadTrack}
              onChange={(e) => setUploadTrack(e.target.value)}
              placeholder="Track name"
              className="glass-input w-full px-3 py-2 text-sm"
            />
          </div>
          <div className="flex-1 w-full space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase">Race</label>
            <input
              type="text"
              value={uploadRace}
              onChange={(e) => setUploadRace(e.target.value)}
              placeholder="Race identifier"
              className="glass-input w-full px-3 py-2 text-sm"
            />
          </div>
          <div className="flex-1 w-full space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase">CSV File</label>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="glass-input w-full px-3 py-1.5 text-sm file:mr-4 file:py-1 file:px-3 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-primary/20 file:text-primary hover:file:bg-primary/30"
            />
          </div>
          <button
            onClick={handleFileUpload}
            className="glass-button px-6 py-2 h-[42px] font-bold whitespace-nowrap bg-primary text-white hover:bg-primary/90 border-primary/50"
            disabled={loading || !file}
          >
            {loading ? "Analyzing..." : "Upload & Analyze"}
          </button>
        </div>

        {track && race && (
          <div className="mt-4 pt-4 border-t border-white/10 flex justify-end">
            <button 
              onClick={loadExistingAnalysis} 
              className="text-sm text-primary hover:text-primary/80 hover:underline flex items-center gap-1"
              disabled={loading}
            >
              <span>Analyze Existing Race Data</span>
              <span>→</span>
            </button>
          </div>
        )}
      </div>

      {loading && (
        <div className="w-full h-[200px] glass-card flex flex-col items-center justify-center text-muted-foreground animate-pulse">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
          <p>Analyzing race data...</p>
        </div>
      )}
      
      {error && (
        <div className="w-full p-4 glass-card bg-destructive/10 border-destructive/20 text-destructive flex items-center gap-3">
          <span className="text-xl">❌</span>
          <span className="font-medium">{error}</span>
        </div>
      )}

      {analysis && (
        <>
          {/* Key Moments */}
          {analysis.key_moments && analysis.key_moments.length > 0 && (
            <div className="glass-card p-6">
              <h4 className="text-lg font-bold text-white mb-4">Key Moments</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {analysis.key_moments.map((moment: any, idx: number) => (
                  <div key={idx} className="p-4 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-colors">
                    <div className="flex justify-between items-start mb-2">
                      <div className="text-xs font-bold text-primary uppercase tracking-wider bg-primary/10 px-2 py-0.5 rounded-full">
                        {moment.type?.replace("_", " ")}
                      </div>
                      {moment.lap && <span className="text-xs font-mono text-muted-foreground">Lap {moment.lap}</span>}
                    </div>
                    <div className="text-sm text-foreground mb-2">{moment.description}</div>
                    <div className="flex justify-between items-center text-xs text-muted-foreground font-mono border-t border-white/5 pt-2 mt-2">
                      {moment.time && <span>T: {moment.time.toFixed(2)}s</span>}
                      {moment.vehicle && <span>{moment.vehicle}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Race Narrative */}
          {aiStory.raceNarrative && (
            <div className="glass-card p-6">
              <h4 className="text-lg font-bold text-white mb-4">Race Narrative</h4>
              <div className="space-y-4 text-muted-foreground leading-relaxed">
                {Array.isArray(aiStory.raceNarrative) ? (
                  aiStory.raceNarrative.map((para: string, idx: number) => (
                    <p key={idx}>{para}</p>
                  ))
                ) : (
                  <p>{String(aiStory.raceNarrative)}</p>
                )}
              </div>
            </div>
          )}

          {/* Strategic Decisions */}
          {aiStory.strategicDecisions && (
            <div className="glass-card p-6 border-l-4 border-l-blue-500">
              <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-blue-500">🧠</span> Strategic Decisions
              </h4>
              <ul className="space-y-2">
                {Array.isArray(aiStory.strategicDecisions) ? (
                  aiStory.strategicDecisions.map((item: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-3 text-muted-foreground">
                      <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-500 flex-shrink-0"></span>
                      <span>{item}</span>
                    </li>
                  ))
                ) : (
                  <li className="flex items-start gap-3 text-muted-foreground">
                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-500 flex-shrink-0"></span>
                    <span>{String(aiStory.strategicDecisions)}</span>
                  </li>
                )}
              </ul>
            </div>
          )}

          {/* Critical Moments */}
          {aiStory.criticalMoments && (
            <div className="glass-card p-6 border-l-4 border-l-amber-500">
              <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <AlertTriangle className="inline-block h-5 w-5 text-amber-500" /> Critical Moments
              </h4>
              <ul className="space-y-2">
                {Array.isArray(aiStory.criticalMoments) ? (
                  aiStory.criticalMoments.map((item: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-3 text-muted-foreground">
                      <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0"></span>
                      <span>{item}</span>
                    </li>
                  ))
                ) : (
                  <li className="flex items-start gap-3 text-muted-foreground">
                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0"></span>
                    <span>{String(aiStory.criticalMoments)}</span>
                  </li>
                )}
              </ul>
            </div>
          )}

          {/* Performance Highlights */}
          {aiStory.performanceHighlights && (
            <div className="glass-card p-6 border-l-4 border-l-emerald-500">
              <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <Star className="inline-block h-5 w-5 text-emerald-500" /> Performance Highlights
              </h4>
              <ul className="space-y-2">
                {Array.isArray(aiStory.performanceHighlights) ? (
                  aiStory.performanceHighlights.map((item: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-3 text-muted-foreground">
                      <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0"></span>
                      <span>{item}</span>
                    </li>
                  ))
                ) : (
                  <li className="flex items-start gap-3 text-muted-foreground">
                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0"></span>
                    <span>{String(aiStory.performanceHighlights)}</span>
                  </li>
                )}
              </ul>
            </div>
          )}

          {/* Lessons Learned */}
          {aiStory.lessonsLearned && (
            <div className="glass-card p-6 border-l-4 border-l-purple-500">
              <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-purple-500">🎓</span> Lessons Learned
              </h4>
              <ul className="space-y-2">
                {Array.isArray(aiStory.lessonsLearned) ? (
                  aiStory.lessonsLearned.map((item: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-3 text-muted-foreground">
                      <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-purple-500 flex-shrink-0"></span>
                      <span>{item}</span>
                    </li>
                  ))
                ) : (
                  <li className="flex items-start gap-3 text-muted-foreground">
                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-purple-500 flex-shrink-0"></span>
                    <span>{String(aiStory.lessonsLearned)}</span>
                  </li>
                )}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default PostEventAnalysis;

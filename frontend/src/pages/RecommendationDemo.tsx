/**
 * Recommendation Demo Page
 * Demonstrates the ARCHE recommendation flow
 */

import React, { useState } from "react";
import { useRecommendations, useExplanation } from "../hooks/useAPI";
import FlowArt, { FlowSection } from "../components/ui/story-scroll";

function formatTrace(trace: string): string[] {
  return trace
    .split(".")
    .map((part) => part.trim())
    .filter(Boolean);
}

export function RecommendationDemo() {
  const { data: recommendations, loading: recLoading, error: recError, fetch: fetchRecommendations } = useRecommendations();
  const { data: explanation, loading: expLoading, fetch: fetchExplanation } = useExplanation();
  const [userToken, setUserToken] = useState("demo-user-001");
  const [selectedRecId, setSelectedRecId] = useState<string | null>(null);

  const handleGetRecommendations = async () => {
    try {
      await fetchRecommendations({
        user_token: userToken,
        n: 5,
        context: { source: "demo" },
      });
    } catch (err) {
      console.error("Failed to get recommendations:", err);
    }
  };

  const handleExplain = async (recId: string) => {
    setSelectedRecId(recId);
    try {
      await fetchExplanation({
        recommendation_id: recId,
        user_token: userToken,
      });
    } catch (err) {
      console.error("Failed to get explanation:", err);
    }
  };

  return (
    <FlowArt aria-label="ARCHE Recommendation Demo">
      <FlowSection aria-label="Hero" style={{ backgroundColor: "#fd5200", color: "#fff" }}>
        <p className="text-xs font-bold uppercase tracking-[0.2em]">01 - Recommendations</p>
        <hr className="my-[2vw] border-none border-t border-white/50" />
        <h1 className="text-[clamp(3.2rem,11vw,11rem)] font-bold leading-[0.86] uppercase tracking-tight">
          Personalized
          <br />
          Insights
        </h1>
        <hr className="my-[2vw] border-none border-t border-white/50" />
        <p className="mt-auto max-w-[55ch] text-[clamp(1rem,2.1vw,1.6rem)] leading-relaxed">
          Your recommendations, explained. Powered by ARCHE memory engine.
        </p>
      </FlowSection>

      <FlowSection aria-label="GetRecommendations" style={{ backgroundColor: "#F5F0E8", color: "#000" }}>
        <div className="max-w-2xl">
          <p className="text-xs font-bold uppercase tracking-[0.2em]">02 - Fetch Recommendations</p>
          <hr className="my-[2vw] border-none border-t border-black/60" />

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold mb-2">User Token</label>
              <input
                type="text"
                value={userToken}
                onChange={(e) => setUserToken(e.target.value)}
                placeholder="Enter user token"
                className="w-full px-4 py-2 border border-black/20 rounded-lg bg-white"
              />
            </div>

            <button
              onClick={handleGetRecommendations}
              disabled={recLoading}
              className="px-6 py-3 bg-[#1A3DE8] text-white font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {recLoading ? "Loading..." : "Get Recommendations"}
            </button>

            {recError && <div className="text-red-600 text-sm font-semibold">{recError}</div>}
          </div>
        </div>
      </FlowSection>

      {recommendations && (
        <FlowSection aria-label="Results" style={{ backgroundColor: "#fff", color: "#000" }}>
          <p className="text-xs font-bold uppercase tracking-[0.2em]">03 - Results</p>
          <hr className="my-[2vw] border-none border-t border-black/60" />

          <div className="space-y-4">
            <div className="bg-gray-100 p-4 rounded-lg">
              <p className="text-xs text-gray-600">User: {recommendations.user_token}</p>
              <p className="text-xs text-gray-600">Simulation Basis: {recommendations.simulation_basis}</p>
              <p className="text-xs text-gray-600">Total Items: {recommendations.recommendations.length}</p>
            </div>

            <div className="space-y-2">
              {recommendations.recommendations.map((rec) => (
                <div key={rec.recommendation_id} className="border border-black/15 rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-semibold">{rec.item_name}</p>
                      <p className="text-sm text-gray-600">{rec.item_category}</p>
                      <p className="text-xs text-gray-500">{rec.recommendation_type}</p>
                      <p className="text-sm mt-2 text-gray-700">{rec.explanation}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold">{(rec.confidence * 100).toFixed(1)}%</p>
                      <button
                        onClick={() => handleExplain(rec.recommendation_id)}
                        disabled={expLoading}
                        className="mt-2 text-xs px-3 py-1 bg-[#1A3DE8] text-white rounded hover:bg-blue-700"
                      >
                        {expLoading && selectedRecId === rec.recommendation_id ? "Loading..." : "Explain"}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </FlowSection>
      )}

      {explanation && (
        <FlowSection aria-label="Explanation" style={{ backgroundColor: "#1A3DE8", color: "#fff" }}>
          <p className="text-xs font-bold uppercase tracking-[0.2em]">04 - Deep Dive</p>
          <hr className="my-[2vw] border-none border-t border-white/50" />

          <div className="space-y-4 max-w-3xl">
            <div>
              <p className="text-sm font-semibold mb-2">Recommendation</p>
              <p className="text-base leading-relaxed">
                {explanation.recommendation.item_name} ({explanation.recommendation.item_category})
              </p>
            </div>

            <div>
              <p className="text-sm font-semibold mb-2">Trace</p>
              <p className="text-base leading-relaxed">{explanation.trace}</p>
            </div>

            {formatTrace(explanation.trace).length > 0 && (
              <div>
                <p className="text-sm font-semibold mb-2">Reasoning Chain (Parsed)</p>
                <ol className="space-y-2">
                  {formatTrace(explanation.trace).map((step, i) => (
                    <li key={i} className="text-sm">
                      {i + 1}. {step}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {explanation.alternatives_considered.length > 0 && (
              <div>
                <p className="text-sm font-semibold mb-2">Alternatives Considered</p>
                <ul className="space-y-1">
                  {explanation.alternatives_considered.map((alt) => (
                    <li key={alt.recommendation_id} className="text-sm">
                      {alt.item_name} ({alt.item_category}) - {(alt.confidence * 100).toFixed(1)}%
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="bg-white/20 rounded-lg p-4">
              <p className="text-xs uppercase tracking-wider">Confidence Score</p>
              <p className="text-2xl font-bold mt-2">{(explanation.recommendation.confidence * 100).toFixed(1)}%</p>
            </div>
          </div>
        </FlowSection>
      )}
    </FlowArt>
  );
}

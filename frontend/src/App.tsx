import { useState } from "react";
import FlowArt, { FlowSection } from "./components/ui/story-scroll";
import { RecommendationDemo } from "./pages/RecommendationDemo";

function App() {
  const [showDemo, setShowDemo] = useState(false);

  if (showDemo) {
    return <RecommendationDemo />;
  }

  return (
    <FlowArt aria-label="ARCHE Story UI">
      <FlowSection aria-label="Hero" style={{ backgroundColor: "#fd5200", color: "#fff" }}>
        <p className="text-xs font-bold uppercase tracking-[0.2em]">01 - ARCHE</p>
        <hr className="my-[2vw] border-none border-t border-black opacity-100" />
        <h1 className="text-[clamp(3.2rem,11vw,11rem)] font-bold leading-[0.86] uppercase tracking-tight">
          Agentic
          <br />
          Memory
          <br />
          Engine
        </h1>
        <hr className="my-[2vw] border-none border-t border-black opacity-100" />
        <p className="mt-auto max-w-[55ch] text-[clamp(1rem,2.1vw,1.6rem)] leading-relaxed">
          Personalized simulation and recommendations with explainability, powered by ARCHE.
        </p>
      </FlowSection>

      <FlowSection aria-label="Features" style={{ backgroundColor: "#F5F0E8", color: "#000" }}>
        <p className="text-xs font-bold uppercase tracking-[0.2em]">02 - Features</p>
        <hr className="my-[2vw] border-none border-t border-black/60" />
        <h2 className="text-[clamp(2.6rem,9vw,8rem)] font-bold leading-[0.88] uppercase tracking-tight">
          Explainable
          <br />
          Recommendations
        </h2>
        <hr className="my-[2vw] border-none border-t border-black/60" />
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-black/15 bg-white/70 p-4">
            <p className="mb-2 text-sm font-bold uppercase tracking-wider">Ingest</p>
            <p className="text-sm leading-relaxed text-black/75">Privacy-aware signal ingestion with deterministic token abstraction.</p>
          </div>
          <div className="rounded-lg border border-black/15 bg-white/70 p-4">
            <p className="mb-2 text-sm font-bold uppercase tracking-wider">Simulate</p>
            <p className="text-sm leading-relaxed text-black/75">Behavior snapshots built from historical memory and context cues.</p>
          </div>
          <div className="rounded-lg border border-black/15 bg-white/70 p-4">
            <p className="mb-2 text-sm font-bold uppercase tracking-wider">Explain</p>
            <p className="text-sm leading-relaxed text-black/75">Human-readable rationale and alternatives for each recommendation.</p>
          </div>
        </div>
      </FlowSection>

      <FlowSection aria-label="CTA" style={{ backgroundColor: "#1A3DE8", color: "#fff" }}>
        <p className="text-xs font-bold uppercase tracking-[0.2em]">03 - Try It</p>
        <hr className="my-[2vw] border-none border-t border-white/50" />
        <h2 className="text-[clamp(2.6rem,9vw,8rem)] font-bold leading-[0.88] uppercase tracking-tight">
          See It
          <br />
          In Action
        </h2>
        <hr className="my-[2vw] border-none border-t border-white/50" />
        <button
          onClick={() => setShowDemo(true)}
          className="mt-4 px-8 py-4 bg-white text-[#1A3DE8] font-bold text-lg rounded-lg hover:bg-gray-200 transition"
        >
          Try Demo →
        </button>
      </FlowSection>
    </FlowArt>
  );
}

export default App;

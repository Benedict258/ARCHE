import FlowArt, { FlowSection } from "../components/ui/story-scroll.tsx";

export default function FlowArtDefaultDemo() {
  return (
    <FlowArt aria-label="Présentation Flow Art">
      <FlowSection aria-label="Qui nous sommes" style={{ backgroundColor: "#fd5200", color: "#fff" }}>
        <p className="text-xs font-bold uppercase tracking-[0.2em]">01 — Who we are</p>
        <hr className="my-[2vw] border-none border-t border-black opacity-100" />
        <div>
          <h1 className="text-[clamp(3.5rem,12vw,14rem)] font-bold leading-[0.85] uppercase tracking-tight">
            Create
            <br />
            Without
            <br />
            Limits
          </h1>
        </div>
        <hr className="my-[2vw] border-none border-t border-black opacity-100" />
        <p className="mt-auto max-w-[50ch] text-[clamp(1rem,2.5vw,2rem)] font-normal leading-relaxed">
          We believe every artist deserves a platform that puts creativity first. No algorithms, no noise — just pure art and the people who make it.
        </p>
      </FlowSection>

      <FlowSection aria-label="La mission" style={{ backgroundColor: "#000", color: "#fff" }}>
        <p className="text-xs font-bold uppercase tracking-[0.2em]">02 — The mission</p>
        <hr className="my-[2vw] border-none border-t border-white/60" />
        <div>
          <h2 className="text-[clamp(3.5rem,12vw,14rem)] font-bold leading-[0.85] uppercase tracking-tight">
            Art
            <br />
            First
            <br />
            Always
          </h2>
        </div>
        <hr className="my-[2vw] border-none border-t border-white/60" />
        <p className="max-w-[50ch] text-[clamp(1rem,2.5vw,2rem)] font-normal leading-relaxed">
          A global community built for artists, by artists. We're rewriting the rules of how creative work gets seen, shared, and valued.
        </p>
      </FlowSection>
    </FlowArt>
  );
}

import { LangProvider, LangToggle } from "./lang";
import VoiceCall from "./voice-call";

export default function Home() {
  return (
    <LangProvider>
      <LangToggle />
      <VoiceCall />
    </LangProvider>
  );
}

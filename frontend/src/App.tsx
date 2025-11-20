import { useState } from "react";
import Navigation from "./components/Navigation";
import HomePage from "./pages/HomePage";
import LiveTelemetryPage from "./pages/LiveTelemetryPage.tsx";
import DriverTrainingPage from "./pages/DriverTrainingPage.tsx";
import PreEventPage from "./pages/PreEventPage.tsx";
import PostEventPage from "./pages/PostEventPage.tsx";
import ShaderBackground from "./components/ui/shader-background";

function App() {
  const [currentPage, setCurrentPage] = useState("home");
  const [track, setTrack] = useState("barber");
  const [race, setRace] = useState("R1");
  const [vehicleId, setVehicleId] = useState("GR86-002-000");

  const renderPage = () => {
    switch (currentPage) {
      case "home":
        return <HomePage onNavigate={setCurrentPage} />;
      case "live":
        return (          <LiveTelemetryPage
            track={track}
            race={race}
            vehicleId={vehicleId}
            onTrackChange={setTrack}
            onRaceChange={setRace}
            onVehicleChange={setVehicleId}
          />
        );
      case "training":
        return (
          <DriverTrainingPage track={track} race={race} vehicleId={vehicleId} />
        );
      case "pre-event":
        return <PreEventPage />;
      case "post-event":
        return <PostEventPage track={track} race={race} />;
      default:
        return <HomePage onNavigate={setCurrentPage} />;
    }
  };

  return (
    <>
      <ShaderBackground />
      <div className="min-h-screen w-full bg-transparent text-foreground font-sans antialiased relative selection:bg-primary/20 selection:text-primary">
        <Navigation currentPage={currentPage} onNavigate={setCurrentPage} />
        <main className="pt-16 w-full">
          {renderPage()}
        </main>
      </div>
    </>
  );
}

export default App;

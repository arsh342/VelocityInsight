import { House, Calendar, CalendarCheck2, Headset } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";

interface NavigationProps {
  currentPage: string;
  onNavigate: (page: string) => void;
}

export default function Navigation({
  currentPage,
  onNavigate,
}: NavigationProps) {
  const MotorRacingHelmet = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-motor-racing-helmet">
      <path d="M22 12.2a10 10 0 1 0-19.4 3.2c.2.5.8 1.1 1.3 1.3l13.2 5.1c.5.2 1.2 0 1.6-.3l2.6-2.6c.4-.4.7-1.2.7-1.7Z"/>
      <path d="m21.8 18-10.5-4a2 2.06 0 0 1 .7-4h9.8"/>
    </svg>
  );

  const pages = [
    { id: "home", label: "Home", icon: <House className="h-5 w-5" /> },
    { id: "training", label: "Driver Training", icon: <MotorRacingHelmet /> },
    { id: "pre-event", label: "Pre-Event", icon: <Calendar className="h-5 w-5" /> },
    { id: "post-event", label: "Post-Event", icon: <CalendarCheck2 className="h-5 w-5" /> },
    { id: "live", label: "Telemetry", icon: <Headset className="h-5 w-5" /> },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 h-16 z-50 bg-black/20 dark:bg-black/20 backdrop-blur-xl border-b border-white/10">
      <div className="container mx-auto h-full flex items-center justify-between px-4">
        <div
          className="flex items-center gap-3 text-xl font-bold text-foreground hover:text-primary transition-colors cursor-pointer group"
          onClick={() => onNavigate("home")}
        >
          <div className="flex items-center gap-2 font-bold text-xl tracking-tight">
            <img src="/logo.jpg" alt="VelocityInsight Logo" className="h-8 w-8 rounded-full object-cover" />
            <span className="hidden md:inline">VelocityInsight</span>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1">
            {pages.map((page) => (
              <button
                key={page.id}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                  currentPage === page.id 
                    ? "bg-primary/10 text-primary shadow-[0_0_15px_rgba(220,38,38,0.2)] border border-primary/20" 
                    : "text-muted-foreground hover:text-foreground hover:bg-accent"
                }`}
                onClick={() => onNavigate(page.id)}
              >
                <span className="text-lg">{page.icon}</span>
                <span className="hidden md:inline">{page.label}</span>
              </button>
            ))}
          </div>
          
          <ThemeToggle />
        </div>
      </div>
    </nav>
  );
}

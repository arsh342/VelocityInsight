import { Target, BarChart3, Zap } from "lucide-react";
import { BentoGrid, BentoCard } from "@/components/ui/bento-grid";
import { GooeyText } from "@/components/ui/gooey-text-morphing";
import { HelmetIcon } from "@/components/icons/HelmetIcon";


interface HomePageProps {
  onNavigate: (page: string) => void;
}

export default function HomePage({ onNavigate }: HomePageProps) {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center p-6 relative z-10">
        {/* Hero Section */}
        <section className="w-full max-w-5xl mx-auto text-center mb-16 animate-in fade-in zoom-in duration-700">
          <div className="flex flex-col items-center justify-center space-y-6">
            <div className="flex items-center justify-center gap-4 mb-4">
            </div>
            
            <div className="h-[120px] md:h-[160px] flex items-center justify-center">
              <GooeyText
                texts={["Speed", "Precision", "Victory", "Excellence"]}
                morphTime={1.2}
                cooldownTime={0.5}
                className="font-bold"
                textClassName="text-5xl md:text-7xl lg:text-8xl font-display tracking-tight bg-gradient-to-b from-foreground to-foreground/60 bg-clip-text"
              />
            </div>
            
            <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto font-light">
              Advanced telemetry analysis and insights for competitive racing
            </p>
            
            <div className="grid grid-cols-3 gap-8 mt-8">
              <div className="flex flex-col items-center p-4 rounded-xl bg-white/5 dark:bg-white/5 border border-white/10 backdrop-blur-sm">
                <span className="text-3xl font-bold text-foreground">7</span>
                <span className="text-xs uppercase tracking-widest text-muted-foreground mt-1">Tracks</span>
              </div>
              <div className="flex flex-col items-center p-4 rounded-xl bg-white/5 dark:bg-white/5 border border-white/10 backdrop-blur-sm">
                <span className="text-3xl font-bold text-foreground">50+</span>
                <span className="text-xs uppercase tracking-widest text-muted-foreground mt-1">Vehicles</span>
              </div>
              <div className="flex flex-col items-center p-4 rounded-xl bg-white/5 dark:bg-white/5 border border-white/10 backdrop-blur-sm">
                <span className="text-3xl font-bold text-foreground">1M+</span>
                <span className="text-xs uppercase tracking-widest text-muted-foreground mt-1">Data Points</span>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section - Bento Grid */}
        <section className="w-full max-w-6xl mx-auto mb-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Core Analytics Features</h2>
            <p className="text-muted-foreground">Powerful tools to elevate your racing performance</p>
          </div>

          <BentoGrid className="lg:grid-rows-3 auto-rows-[22rem]">
            <BentoCard
              name="Driver Training"
              className="lg:row-start-1 lg:row-end-4 lg:col-start-2 lg:col-end-3"
              background={
                <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-primary/5 to-transparent opacity-50" />
              }
              Icon={Target}
              description="Comprehensive performance analysis to identify improvement areas. Optimize your racing line, analyze sector times, and master every corner."
              cta="Start Training"
              onClick={() => onNavigate("training")}
            />
            
            <BentoCard
              name="Pre-Event Prediction"
              className="lg:col-start-1 lg:col-end-2 lg:row-start-1 lg:row-end-3"
              background={
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-transparent to-transparent" />
              }
              Icon={BarChart3}
              description="Forecasting before the green flag. Predict qualifying, race pace, and tire degradation with machine learning."
              cta="View Predictions"
              onClick={() => onNavigate("pre-event")}
            />
            
            <BentoCard
              name="Post-Event Analysis"
              className="lg:col-start-1 lg:col-end-2 lg:row-start-3 lg:row-end-4"
              background={
                <div className="absolute inset-0 bg-gradient-to-tr from-purple-500/10 via-transparent to-transparent" />
              }
              Icon={BarChart3}
              description="Comprehensive race storytelling with insights. Discover key moments and strategic decisions that defined the race."
              cta="Analyze Race"
              onClick={() => onNavigate("post-event")}
            />
            
            <BentoCard
              name="Real-Time Processing"
              className="lg:col-start-3 lg:col-end-3 lg:row-start-1 lg:row-end-2"
              background={
                <div className="absolute inset-0 bg-gradient-to-bl from-green-500/10 via-transparent to-transparent" />
              }
              Icon={Zap}
              description="Lightning-fast analysis of millions of telemetry data points in seconds using optimized pipelines."
              cta="Learn More"
              onClick={() => onNavigate("training")}
            />
            
            <BentoCard
              name="Google Gemini"
              className="lg:col-start-3 lg:col-end-3 lg:row-start-2 lg:row-end-4"
              background={
                <div className="absolute inset-0 bg-gradient-to-tl from-amber-500/10 via-transparent to-transparent" />
              }
              Icon={HelmetIcon}
              description="State-of-the-art artificial intelligence providing personalized recommendations and predictive analytics for competitive advantage."
              cta="Explore"
              onClick={() => onNavigate("pre-event")}
            />
          </BentoGrid>
        </section>
        
        {/* Quick Start Guide */}
        <section className="w-full max-w-6xl mx-auto mb-16">
          <div className="glass-card p-10">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Quick Start Guide</h2>
              <p className="text-muted-foreground">Get started in 3 simple steps</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 rounded-full bg-primary/20 border-2 border-primary flex items-center justify-center text-primary text-2xl font-bold mb-4">
                  1
                </div>
                <h3 className="font-bold text-gray-900 dark:text-white mb-2">Select Your Track</h3>
                <p className="text-sm text-muted-foreground">
                  Choose from 7 iconic racing circuits including Barber, Indianapolis, COTA, and more
                </p>
              </div>
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 rounded-full bg-primary/20 border-2 border-primary flex items-center justify-center text-primary text-2xl font-bold mb-4">
                  2
                </div>
                <h3 className="font-bold text-gray-900 dark:text-white mb-2">Pick Your Analysis</h3>
                <p className="text-sm text-muted-foreground">
                  Choose between training optimization, pre-event predictions, or post-race analysis
                </p>
              </div>
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 rounded-full bg-primary/20 border-2 border-primary flex items-center justify-center text-primary text-2xl font-bold mb-4">
                  3
                </div>
                <h3 className="font-bold text-gray-900 dark:text-white mb-2">Get Insights</h3>
                <p className="text-sm text-muted-foreground">
                  Receive personalized recommendations and actionable insights powered by Google Gemini
                </p>
              </div>
            </div>
          </div>
        </section>
    </div>
  );
}

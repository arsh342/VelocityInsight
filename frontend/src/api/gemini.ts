/**
 * Gemini API Service for AI-powered insights and summarization
 */
import { GoogleGenerativeAI } from "@google/generative-ai";

const GEMINI_API_KEY = "AIzaSyBCRy3L5lLJOI68eeR_HICYq8Tz66Dj_Hc";
const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

interface RaceInsights {
  summary: string;
  keyInsights: string[];
  recommendations: string[];
  strategicAdvice: string;
}

interface PerformanceData {
  lapTimes?: any[];
  degradation?: any;
  consistency?: any;
  pitStrategy?: any;
  predictions?: any;
}

/**
 * Generate AI-powered race insights using Gemini
 */
export async function generateRaceInsights(
  track: string,
  race: string,
  vehicleId: string,
  performanceData: PerformanceData
): Promise<RaceInsights> {
  try {
    const model = genAI.getGenerativeModel({ model: "gemini-pro" });

    const prompt = `
You are an expert Formula 1 race engineer analyzing telemetry data for a GR Cup race.

TRACK: ${track}
RACE: ${race}
VEHICLE: ${vehicleId}

PERFORMANCE DATA:
${JSON.stringify(performanceData, null, 2)}

Analyze this data and provide:
1. A concise 2-3 sentence summary of the driver's performance
2. 3-5 key insights about their driving style, tire management, or pace
3. 3-5 actionable recommendations for improving lap times or race strategy
4. Strategic advice for the remaining race

Format your response as JSON:
{
  "summary": "Brief summary...",
  "keyInsights": ["Insight 1", "Insight 2", ...],
  "recommendations": ["Recommendation 1", "Recommendation 2", ...],
  "strategicAdvice": "Strategic advice paragraph..."
}

Be specific, technical, and actionable. Use F1 terminology.
`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    const text = response.text();

    // Try to extract JSON from the response
    let insights: RaceInsights;
    try {
      // Remove markdown code blocks if present
      const cleanedText = text
        .replace(/```json\n?/g, "")
        .replace(/```\n?/g, "")
        .trim();
      insights = JSON.parse(cleanedText);
    } catch (e) {
      // Fallback: parse manually if JSON parsing fails
      insights = {
        summary:
          text.split("SUMMARY:")[1]?.split("\n")[0] || text.substring(0, 200),
        keyInsights: extractListItems(text, "INSIGHTS", "RECOMMENDATIONS"),
        recommendations: extractListItems(text, "RECOMMENDATIONS", "STRATEGIC"),
        strategicAdvice:
          text.split("STRATEGIC")[1] || text.substring(text.length - 200),
      };
    }

    return insights;
  } catch (error) {
    console.error("Error generating insights:", error);
    return {
      summary: "Unable to generate AI insights at this time.",
      keyInsights: [],
      recommendations: [],
      strategicAdvice: "Please check your connection and try again.",
    };
  }
}

/**
 * Generate strategic instructions based on current race situation
 */
export async function generateStrategicInstructions(
  track: string,
  race: string,
  vehicleId: string,
  currentLap: number,
  tireAge: number,
  position: number,
  gapToLeader: number
): Promise<string> {
  try {
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

    const prompt = `
You are a Formula 1 race engineer giving real-time instructions to your driver.

SITUATION:
- Track: ${track}
- Race: ${race}
- Vehicle: ${vehicleId}
- Current Lap: ${currentLap}
- Tire Age: ${tireAge} laps
- Position: ${position}
- Gap to Leader: ${gapToLeader}s

Provide a brief, actionable instruction (2-3 sentences) for what the driver should do right now.
Be decisive and specific. Use F1 terminology.

Examples:
- "Push for 3 laps to close the gap, then manage tires"
- "Box this lap for fresh tires, undercut opportunity"
- "Conserve tires, maintain position until lap 20"

Respond with ONLY the instruction, no extra formatting.
`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    return response.text().trim();
  } catch (error) {
    console.error("Error generating strategic instructions:", error);
    return "Continue current pace and monitor tire degradation.";
  }
}

/**
 * Summarize telemetry data for quick insights
 */
export async function summarizeTelemetry(
  telemetryData: any[],
  track: string
): Promise<string> {
  try {
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

    const sampleData = telemetryData.slice(0, 100); // Use first 100 points

    const prompt = `
Analyze this telemetry data from ${track} and provide a 1-sentence summary highlighting:
- Average speed
- Throttle/brake patterns
- Any anomalies or notable patterns

Telemetry data (sample):
${JSON.stringify(sampleData, null, 2)}

Respond with a single sentence summary.
`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    return response.text().trim();
  } catch (error) {
    console.error("Error summarizing telemetry:", error);
    return "Telemetry data analyzed successfully.";
  }
}

function extractListItems(
  text: string,
  startMarker: string,
  endMarker: string
): string[] {
  const startIndex = text.indexOf(startMarker);
  const endIndex = text.indexOf(endMarker);

  if (startIndex === -1) return [];

  const section =
    endIndex === -1
      ? text.substring(startIndex)
      : text.substring(startIndex, endIndex);

  // Extract bullet points or numbered items
  const items =
    section.match(/[-*•]\s*(.+?)(?:\n|$)/g) ||
    section.match(/\d+\.\s*(.+?)(?:\n|$)/g) ||
    [];

  return items
    .map((item) => item.replace(/[-*•\d.\s]/g, "").trim())
    .filter(Boolean);
}

/**
 * Clean markdown formatting from AI responses
 */
function cleanMarkdownFormatting(text: string): string {
  return (
    text
      // Remove markdown code blocks
      .replace(/```[a-z]*\n?/gi, "")
      // Remove bold/italic asterisks and underscores
      .replace(/(\*\*|__)(.*?)\1/g, "$2")
      .replace(/(\*|_)(.*?)\1/g, "$2")
      // Remove markdown headers (keep the text)
      .replace(/^#{1,6}\s+/gm, "")
      // Clean up extra whitespace
      .replace(/\n{3,}/g, "\n\n")
      .trim()
  );
}

/**
 * Generate driver training insights
 */
export async function generateDriverTrainingInsights(
  track: string,
  race: string,
  vehicleId: string,
  performanceData: any
): Promise<string> {
  try {
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

    const prompt = `
You are a professional racing coach with expertise in GR Cup competition and driver development, analyzing telemetry for performance optimization.

SESSION DETAILS:
- Circuit: ${track}
- Race: ${race}
- Vehicle: ${vehicleId}
- Telemetry Data: ${JSON.stringify(performanceData, null, 2)}

Provide expert-level driver coaching analysis:

DRIVING TECHNIQUE ASSESSMENT:
- Analyze braking efficiency: brake point consistency, trail-braking technique, and brake release timing
- Evaluate cornering technique: turn-in points, apex hitting accuracy, and exit acceleration patterns
- Assess throttle application: progressive vs aggressive inputs, traction management, and power delivery optimization
- Review racing line efficiency: deviation from optimal path, sector-specific line choices

PERFORMANCE OPTIMIZATION:
- Identify the top 3 specific corners or sectors with the highest improvement potential
- Calculate potential lap time gains from technique improvements
- Compare current performance to theoretical optimum lap
- Highlight consistency patterns and areas of variance

TARGETED TRAINING PROGRAM:
- Design specific simulator exercises for identified weaknesses
- Recommend track walking focus points for the next session
- Suggest pedal technique drills for improved car control
- Propose reference driver comparisons for learning

RACE CRAFT DEVELOPMENT:
- Assess tire management skills based on degradation patterns
- Evaluate fuel management and pace optimization
- Review overtaking preparation and defensive positioning
- Analyze adaptation to changing track conditions

MENTAL PERFORMANCE:
- Identify pressure points where performance drops
- Suggest visualization techniques for challenging sections
- Recommend confidence-building exercises for weak areas
- Provide race weekend mental preparation strategies

Write with the authority of a professional motorsport coach. Use specific technical terms and quantified improvement targets. Structure as a comprehensive coaching debrief without formatting markup.
`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    return cleanMarkdownFormatting(response.text());
  } catch (error) {
    console.error("Error generating driver training insights:", error);
    return "Unable to generate training insights at this time.";
  }
}

/**
 * Generate pre-event predictions and insights
 */
export async function generatePreEventInsights(
  track: string,
  weather: string,
  trackTemp: number,
  predictionData: any
): Promise<string> {
  try {
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

    const prompt = `
You are a GR Cup race strategist. Provide CONCISE, ACTIONABLE insights for ${track}.

CONDITIONS: ${weather}, ${trackTemp}°C
DATA: ${JSON.stringify(predictionData, null, 2)}

Provide brief, bullet-pointed insights. Use **bold** for critical information. Keep it SHORT and focused on essentials only.

**PERFORMANCE EXPECTATIONS** (3-4 bullets max):
• Expected qualifying lap time
• Race pace estimate
• Key degradation factors

**TIRE STRATEGY** (3-4 bullets max):
• Degradation rate estimate
• Optimal pit window
• Temperature impact on tires

**RACE STRATEGY** (3-4 bullets max):
• Primary strategy recommendation
• Key decision points (by lap number)
• Setup adjustments needed

**RISK & OPPORTUNITIES** (2-3 bullets max):
• Main overtaking zones
• Track-specific hazards to avoid
• Contingency for weather/SC

Format with markdown bullets (•) and **bold** for important data (lap times, lap numbers, critical warnings).
Keep total response under 15 bullets. Be specific and quantitative.
`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    return response.text();
  } catch (error) {
    console.error("Error generating pre-event insights:", error);
    return "Unable to generate predictions at this time.";
  }
}

/**
 * Generate post-event race analysis and story
 */
export async function generatePostEventInsights(
  track: string,
  race: string,
  analysisData: any
): Promise<string> {
  try {
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

    const prompt = `
You are an F1 race analyst writing a comprehensive post-race report.

RACE: ${race} at ${track}

RACE DATA:
${JSON.stringify(analysisData, null, 2)}

Write a compelling race story that includes:
1. Opening narrative - set the scene and context
2. Key moments and turning points in the race
3. Strategic decisions that influenced the outcome
4. Driver performances and standout efforts
5. Technical insights (tire strategy, pit stops, pace)
6. Lessons learned and takeaways

Write in an engaging, journalistic style like an F1 race report. Make it interesting to read while being technically accurate.
DO NOT use markdown formatting, asterisks, or special characters.
`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    return cleanMarkdownFormatting(response.text());
  } catch (error) {
    console.error("Error generating post-event insights:", error);
    return "Unable to generate race analysis at this time.";
  }
}

export default {
  generateRaceInsights,
  generateStrategicInstructions,
  summarizeTelemetry,
  generateDriverTrainingInsights,
  generatePreEventInsights,
  generatePostEventInsights,
};

"use client"

import { MeshGradient } from "@paper-design/shaders-react"
import { useTheme } from "@/contexts/ThemeProvider"

export default function ShaderBackground() {
  const { theme } = useTheme()
  
  // Light theme: soft pastels and bright colors
  const lightColors = ["#e0f2fe", "#dbeafe", "#e0e7ff", "#f3e8ff", "#fce7f3", "#ffe4e6"]
  // Dark theme: deep blues and teals
  const darkColors = ["#1a1a2a", "#2a3a4a", "#3a4a5a", "#4a5a6a", "#2a4a5a", "#3a5a4a"]
  
  return (
    <div className={`w-full h-full fixed inset-0 -z-10 ${theme === 'light' ? 'bg-gray-50' : 'bg-black'}`}>
      <MeshGradient
        className="w-full h-full absolute inset-0"
        colors={theme === 'light' ? lightColors : darkColors}
        speed={0.42}
        distortion={0.8}
        swirl={0.6}
        grainMixer={0}
        grainOverlay={0}
      />
      
      {/* Subtle veil overlay for better text readability */}
      <div className={`absolute inset-0 pointer-events-none ${theme === 'light' ? 'bg-white/20' : 'bg-black/15'}`} />
      
      {/* Enhanced lighting overlay effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className={`absolute top-1/4 left-1/3 w-96 h-96 rounded-full blur-3xl animate-pulse ${theme === 'light' ? 'bg-blue-300/20' : 'bg-primary/12'}`} style={{ animationDuration: '6s' }} />
        <div className={`absolute bottom-1/3 right-1/4 w-64 h-64 rounded-full blur-2xl animate-pulse ${theme === 'light' ? 'bg-purple-300/15' : 'bg-blue-400/8'}`} style={{ animationDuration: '4s', animationDelay: '1s' }} />
        <div className={`absolute top-1/2 right-1/3 w-48 h-48 rounded-full blur-xl animate-pulse ${theme === 'light' ? 'bg-pink-300/15' : 'bg-primary/10'}`} style={{ animationDuration: '8s', animationDelay: '0.5s' }} />
      </div>
    </div>
  )
}

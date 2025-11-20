import { Moon, Sun } from "lucide-react"
import { useTheme } from "@/contexts/ThemeProvider"

export function ThemeToggle() {
  const { toggleTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      className="relative inline-flex items-center justify-center p-2 rounded-lg border border-white/10 bg-white/5 backdrop-blur-sm hover:bg-white/10 transition-all duration-300 group"
      aria-label="Toggle theme"
    >
      <Sun className="h-5 w-5 text-primary rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-5 w-5 text-primary rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">Toggle theme</span>
    </button>
  )
}

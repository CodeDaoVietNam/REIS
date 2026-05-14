import { NavLink } from 'react-router-dom';
import { Search, Bell, Settings, LayoutDashboard, BarChart3, Map as MapIcon, ShieldAlert, Sun, Moon, Home, GitCompareArrows } from 'lucide-react';
import { cn } from '@/src/lib/utils';
import { useTheme } from '@/src/contexts/useTheme';

export function Navigation() {
  const { theme, toggleTheme } = useTheme();

  return (
    <>
      {/* Full Width Sticky Navigation */}
      <header className="fixed top-0 left-0 w-full z-50 flex justify-between items-center px-8 py-3 bg-surface-container-low/85 backdrop-blur-3xl border-b border-outline-variant/20 shadow-sm">
        <div className="flex items-center gap-12">
          {/* Logo REIS Phóng to & Nổi trội */}
          <NavLink to="/" className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary tracking-tighter drop-shadow-sm select-none cursor-pointer">
            REIS<span className="text-on-surface">.</span>
          </NavLink>
          
          <nav className="hidden md:flex items-center gap-10">
            <NavLink to="/" className={({ isActive }) => cn(
              "text-sm font-medium tracking-wide transition-all duration-300 relative py-1",
              isActive ? "text-primary after:content-[''] after:absolute after:left-0 after:bottom-0 after:w-full after:h-[2px] after:bg-primary after:rounded-full" : "text-on-surface-variant hover:text-on-surface"
            )}>
              Home
            </NavLink>
            <NavLink to="/dashboard" className={({ isActive }) => cn(
              "text-sm font-medium tracking-wide transition-all duration-300 relative py-1",
              isActive ? "text-primary after:content-[''] after:absolute after:left-0 after:bottom-0 after:w-full after:h-[2px] after:bg-primary after:rounded-full" : "text-on-surface-variant hover:text-on-surface"
            )}>
              Dashboard
            </NavLink>
            <NavLink to="/analytics" className={({ isActive }) => cn(
              "text-sm font-medium tracking-wide transition-all duration-300 relative py-1",
              isActive ? "text-primary after:content-[''] after:absolute after:left-0 after:bottom-0 after:w-full after:h-[2px] after:bg-primary after:rounded-full" : "text-on-surface-variant hover:text-on-surface"
            )}>
              Analytics
            </NavLink>
            <NavLink to="/compare" className={({ isActive }) => cn(
              "text-sm font-medium tracking-wide transition-all duration-300 relative py-1",
              isActive ? "text-primary after:content-[''] after:absolute after:left-0 after:bottom-0 after:w-full after:h-[2px] after:bg-primary after:rounded-full" : "text-on-surface-variant hover:text-on-surface"
            )}>
              Compare
            </NavLink>
            <NavLink to="/map" className={({ isActive }) => cn(
              "text-sm font-medium tracking-wide transition-all duration-300 relative py-1",
              isActive ? "text-primary after:content-[''] after:absolute after:left-0 after:bottom-0 after:w-full after:h-[2px] after:bg-primary after:rounded-full" : "text-on-surface-variant hover:text-on-surface"
            )}>
              Map
            </NavLink>
            <NavLink to="/alerts" className={({ isActive }) => cn(
              "text-sm font-medium tracking-wide transition-all duration-300 relative py-1",
              isActive ? "text-primary after:content-[''] after:absolute after:left-0 after:bottom-0 after:w-full after:h-[2px] after:bg-primary after:rounded-full" : "text-on-surface-variant hover:text-on-surface"
            )}>
              Alerts
            </NavLink>
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden lg:flex items-center bg-surface-container-highest/60 rounded-full px-4 py-2 border border-outline-variant/30 transition-all hover:bg-surface-container-highest focus-within:ring-2 ring-primary/30">
            <Search className="w-4 h-4 text-on-surface-variant mr-3" />
            <input 
              className="bg-transparent border-none focus:ring-0 text-sm text-on-surface placeholder:text-on-surface-variant/50 w-48 font-mono outline-none" 
              placeholder="Ctrl+K để tìm..." 
              type="text"
            />
          </div>
          
          {/* Nút đổi Theme */}
          <button 
            onClick={toggleTheme}
            className="p-3 ml-2 bg-surface-container-highest/30 hover:bg-surface-container-highest/80 rounded-full transition-all active:scale-95 border border-transparent hover:border-outline-variant/30"
            title="Chuyển chế độ hiển thị"
          >
            {theme === 'dark' ? (
              <Sun className="w-5 h-5 text-warning" />
            ) : (
              <Moon className="w-5 h-5 text-secondary" />
            )}
          </button>

          <button className="p-3 bg-surface-container-highest/30 hover:bg-surface-container-highest/80 rounded-full transition-all active:scale-95 border border-transparent hover:border-outline-variant/30">
            <Bell className="w-5 h-5 text-on-surface-variant hover:text-primary" />
          </button>
          <button className="p-3 bg-surface-container-highest/30 hover:bg-surface-container-highest/80 rounded-full transition-all active:scale-95 border border-transparent hover:border-outline-variant/30">
            <Settings className="w-5 h-5 text-on-surface-variant hover:text-primary" />
          </button>
        </div>
      </header>

      {/* Spacer to prevent content overlap with fixed header */}
      <div className="h-[76px]"></div>

      {/* Bottom Navigation for Mobile */}
      <nav className="fixed bottom-4 left-4 right-4 z-50 flex justify-around items-center px-4 py-4 md:hidden bg-surface-container-low/90 backdrop-blur-2xl border border-outline-variant/20 shadow-2xl rounded-3xl">
        <NavLink to="/" className={({ isActive }) => cn(
          "flex flex-col items-center justify-center transition-all p-2 rounded-xl",
          isActive ? "text-primary bg-primary/10" : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50"
        )}>
          <Home className="w-6 h-6" />
        </NavLink>
        <NavLink to="/dashboard" className={({ isActive }) => cn(
          "flex flex-col items-center justify-center transition-all p-2 rounded-xl",
          isActive ? "text-primary bg-primary/10" : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50"
        )}>
          <LayoutDashboard className="w-6 h-6" />
        </NavLink>
        <NavLink to="/analytics" className={({ isActive }) => cn(
          "flex flex-col items-center justify-center transition-all p-2 rounded-xl",
          isActive ? "text-primary bg-primary/10" : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50"
        )}>
          <BarChart3 className="w-6 h-6" />
        </NavLink>
        <NavLink to="/compare" className={({ isActive }) => cn(
          "flex flex-col items-center justify-center transition-all p-2 rounded-xl",
          isActive ? "text-primary bg-primary/10" : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50"
        )}>
          <GitCompareArrows className="w-6 h-6" />
        </NavLink>
        <NavLink to="/map" className={({ isActive }) => cn(
          "flex flex-col items-center justify-center transition-all p-2 rounded-xl",
          isActive ? "text-primary bg-primary/10" : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50"
        )}>
          <MapIcon className="w-6 h-6" />
        </NavLink>
        <NavLink to="/alerts" className={({ isActive }) => cn(
          "flex flex-col items-center justify-center transition-all p-2 rounded-xl",
          isActive ? "text-primary bg-primary/10" : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50"
        )}>
          <ShieldAlert className="w-6 h-6" />
        </NavLink>
      </nav>
    </>
  );
}

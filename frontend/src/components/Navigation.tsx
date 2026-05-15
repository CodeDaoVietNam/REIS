import { useEffect, useMemo, useRef, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Search, Bell, Settings, LayoutDashboard, BarChart3, Map as MapIcon, ShieldAlert, Sun, Moon, Home, GitCompareArrows, Info, X } from 'lucide-react';
import { cn } from '@/src/lib/utils';
import { useTheme } from '@/src/contexts/useTheme';
import { PROVINCES } from '@/src/mocks/mockData';

const PAGE_RESULTS = [
  { label: 'Dashboard', path: '/dashboard', hint: 'Tổng quan realtime' },
  { label: 'Analytics', path: '/analytics', hint: 'Phân tích tỉnh' },
  { label: 'Compare', path: '/compare', hint: 'So sánh nhiều tỉnh' },
  { label: 'Map', path: '/map', hint: 'Bản đồ toàn quốc' },
  { label: 'Alerts', path: '/alerts', hint: 'Cảnh báo sức khỏe' },
  { label: 'About', path: '/about', hint: 'Kiến trúc hệ thống' },
];

export function Navigation() {
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [search, setSearch] = useState('');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const searchResults = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return [];

    const pageResults = PAGE_RESULTS
      .filter((item) => item.label.toLowerCase().includes(query) || item.hint.toLowerCase().includes(query))
      .map((item) => ({ ...item, kind: 'Page' }));
    const provinceResults = PROVINCES
      .filter((province) => `${province.name} ${province.en_name}`.toLowerCase().includes(query))
      .slice(0, 6)
      .map((province) => ({
        label: province.name,
        path: `/dashboard?province=${province.id}`,
        hint: `${province.en_name} · ${province.region}`,
        kind: 'Province',
      }));

    return [...pageResults, ...provinceResults].slice(0, 8);
  }, [search]);

  function goTo(path: string) {
    navigate(path);
    setSearch('');
    setSettingsOpen(false);
  }

  useEffect(() => {
    function handleShortcut(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        searchInputRef.current?.focus();
      }
    }

    window.addEventListener('keydown', handleShortcut);
    return () => window.removeEventListener('keydown', handleShortcut);
  }, []);

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
            <NavLink to="/about" className={({ isActive }) => cn(
              "text-sm font-medium tracking-wide transition-all duration-300 relative py-1",
              isActive ? "text-primary after:content-[''] after:absolute after:left-0 after:bottom-0 after:w-full after:h-[2px] after:bg-primary after:rounded-full" : "text-on-surface-variant hover:text-on-surface"
            )}>
              About
            </NavLink>
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative hidden lg:flex items-center bg-surface-container-highest/60 rounded-full px-4 py-2 border border-outline-variant/30 transition-all hover:bg-surface-container-highest focus-within:ring-2 ring-primary/30">
            <Search className="w-4 h-4 text-on-surface-variant mr-3" />
            <input 
              ref={searchInputRef}
              className="bg-transparent border-none focus:ring-0 text-sm text-on-surface placeholder:text-on-surface-variant/50 w-48 font-mono outline-none" 
              placeholder="Ctrl+K để tìm..." 
              type="text"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && searchResults[0]) {
                  goTo(searchResults[0].path);
                }
                if (event.key === 'Escape') setSearch('');
              }}
            />
            {search && (
              <button type="button" onClick={() => setSearch('')} className="text-on-surface-variant hover:text-on-surface">
                <X className="h-4 w-4" />
              </button>
            )}
            {searchResults.length > 0 && (
              <div className="absolute right-0 top-12 z-[60] w-[360px] overflow-hidden rounded-3xl border border-outline-variant/30 bg-surface-container-low shadow-2xl">
                {searchResults.map((item) => (
                  <button
                    key={`${item.kind}-${item.path}-${item.label}`}
                    type="button"
                    onClick={() => goTo(item.path)}
                    className="flex w-full items-center justify-between gap-3 border-b border-outline-variant/10 px-4 py-3 text-left transition last:border-b-0 hover:bg-surface-container-high"
                  >
                    <span>
                      <span className="block font-bold">{item.label}</span>
                      <span className="text-xs text-on-surface-variant">{item.hint}</span>
                    </span>
                    <span className="rounded-full bg-primary/10 px-2 py-1 text-[10px] font-mono uppercase text-primary">{item.kind}</span>
                  </button>
                ))}
              </div>
            )}
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

          <button
            type="button"
            onClick={() => navigate('/alerts')}
            title="Mở trung tâm cảnh báo"
            className="p-3 bg-surface-container-highest/30 hover:bg-surface-container-highest/80 rounded-full transition-all active:scale-95 border border-transparent hover:border-outline-variant/30"
          >
            <Bell className="w-5 h-5 text-on-surface-variant hover:text-primary" />
          </button>
          <div className="relative">
          <button
            type="button"
            onClick={() => setSettingsOpen((current) => !current)}
            title="Thiết lập nhanh"
            className="p-3 bg-surface-container-highest/30 hover:bg-surface-container-highest/80 rounded-full transition-all active:scale-95 border border-transparent hover:border-outline-variant/30"
          >
            <Settings className="w-5 h-5 text-on-surface-variant hover:text-primary" />
          </button>
          {settingsOpen && (
            <div className="absolute right-0 top-14 z-[60] w-80 rounded-3xl border border-outline-variant/30 bg-surface-container-low p-4 shadow-2xl">
              <div className="mb-3 flex items-center justify-between">
                <p className="font-black">Thiết lập nhanh</p>
                <button type="button" onClick={() => setSettingsOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <X className="h-4 w-4" />
                </button>
              </div>
              <div className="space-y-3 text-sm">
                <button
                  type="button"
                  onClick={toggleTheme}
                  className="flex w-full items-center justify-between rounded-2xl bg-surface-container-high px-3 py-3 text-left"
                >
                  <span>Theme</span>
                  <span className="font-mono text-primary">{theme}</span>
                </button>
                <div className="rounded-2xl bg-surface-container-high px-3 py-3">
                  <p className="font-bold">Nguồn dữ liệu</p>
                  <p className="mt-1 text-xs text-on-surface-variant">REST API + WebSocket, fallback mock khi backend tắt.</p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setSettingsOpen(false);
                    navigate('/about');
                  }}
                  className="w-full rounded-2xl border border-primary/30 px-3 py-3 text-left font-bold text-primary"
                >
                  Xem kiến trúc hệ thống
                </button>
              </div>
            </div>
          )}
          </div>
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
        <NavLink to="/about" className={({ isActive }) => cn(
          "flex flex-col items-center justify-center transition-all p-2 rounded-xl",
          isActive ? "text-primary bg-primary/10" : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50"
        )}>
          <Info className="w-6 h-6" />
        </NavLink>
      </nav>
    </>
  );
}

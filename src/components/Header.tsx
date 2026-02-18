
import React, { useState } from 'react';
import { Menu, X, Moon, Sun, ChevronDown } from 'lucide-react';
import logoMobile from '../assets/logo_mobile.png';
import logoStacked from '../assets/logo_stacked.png';
import logoMobileDark from '../assets/logo_mobile_dark.png';
import logoStackedDark from '../assets/logo_stacked_dark.png';

interface HeaderProps {
  onToggleTheme: () => void;
  isDark: boolean;
}

const Header: React.FC<HeaderProps> = ({ onToggleTheme, isDark }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navLinks = [
    { name: 'Forsiden', href: '#', active: true },
    { name: 'Kart', href: '#' },
    { name: 'Markedsrapporter', href: '#', hasDropdown: true },
    { name: 'Innsikt', href: '#' },
    { name: 'Blogg', href: '#', hasDropdown: true },
  ];

  return (
    <header className="bg-base border-b border-br-subtle sticky top-0 z-[100] h-[44px] md:h-[72px] flex items-center transition-all duration-300">
      {/* Containeren har samme max-width som hovedinnholdet (1700px) og er sentrert */}
      <div className="w-full max-w-[1700px] mx-auto px-3 md:px-14 flex items-center justify-between h-full">

        {/* Logo-seksjon */}
        <div className="flex items-center group cursor-pointer shrink-0">
          <img
            src={isDark ? logoMobileDark : logoMobile}
            alt="Innsikt"
            className="h-7 md:hidden"
          />
          <img
            src={isDark ? logoStackedDark : logoStacked}
            alt="Innsikt"
            className="h-12 hidden md:block"
          />
        </div>

        {/* Desktop Links (Skjult på mobil) */}
        <nav className="hidden lg:flex items-center gap-8 ml-12">
          {navLinks.map((link) => (
            <a
              key={link.name}
              href={link.href}
              className={`text-[0.875rem] font-normal transition-all flex items-center gap-1.5 hover:text-accent ${
                link.active ? 'text-accent' : 'text-tx-muted'
              }`}
            >
              {link.name}
              {link.hasDropdown && <ChevronDown className="w-3.5 h-3.5 opacity-50" />}
            </a>
          ))}
        </nav>

        {/* Right side utilities / Mobile Center Button */}
        <div className="flex-1 flex justify-center lg:justify-end items-center gap-2 md:gap-4 px-1">
          {/* Senter-knapp på mobil, høyre-justert på desktop */}
          <button className="bg-positive hover:opacity-90 text-white px-3 md:px-6 py-1.5 md:py-2.5 rounded-md md:rounded-lg text-[0.6875rem] font-semibold uppercase tracking-[0.08em] transition-all active:scale-95 shadow-lg shadow-black/10 whitespace-nowrap">
            Få verdivurdering
          </button>

          <button
            onClick={onToggleTheme}
            className="flex items-center justify-center w-8 h-8 lg:w-10 lg:h-10 rounded-full border border-br-subtle text-tx-muted hover:bg-elevated transition-all hover:text-accent"
          >
            {isDark ? <Sun className="w-4 h-4 lg:w-4.5 lg:h-4.5" /> : <Moon className="w-4 h-4 lg:w-4.5 lg:h-4.5" />}
          </button>
        </div>

        {/* Hamburger Menu Icon - kun synlig på mobil/tablet */}
        <button
          className="lg:hidden p-1.5 text-tx-muted shrink-0"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? <X className="w-5 h-5 md:w-6 md:h-6" /> : <Menu className="w-5 h-5 md:w-6 md:h-6" />}
        </button>
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div className="lg:hidden absolute top-[44px] left-0 w-full bg-base border-b border-br-subtle shadow-2xl animate-in slide-in-from-top duration-300">
          <nav className="flex flex-col p-6 space-y-4">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                className={`text-[1rem] font-normal py-2 border-b border-br-subtle ${
                  link.active ? 'text-accent' : 'text-tx-primary'
                }`}
              >
                {link.name}
              </a>
            ))}
          </nav>
        </div>
      )}
    </header>
  );
};

export default Header;

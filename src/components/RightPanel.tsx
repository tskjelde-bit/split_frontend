
import React, { useState } from 'react';
import { ArrowRight, ChevronRight } from 'lucide-react';
import articleMockup from '../assets/article_mockup.jpg';

const RightPanel: React.FC<{ className?: string }> = ({ className }) => {
  const [email, setEmail] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  // Redusert antall innlegg for å unngå scrolling
  const posts = [
    {
      date: 'JAN 12',
      category: 'MARKEDSINNSIKT',
      title: 'Boligpriser Oslo 2026–2028: Analyse av ferske prognoser',
      image: articleMockup,
      featured: true,
    },
    {
      date: 'JAN 05',
      category: 'MARKEDSINNSIKT',
      title: 'Hvordan vil utviklingen i styringsrenta påvirke boligprisene fremover?',
      featured: false,
    }
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setEmail('');
    alert('Takk for din påmelding.');
  };

  return (
    <aside className={`bg-surface flex flex-col h-full overflow-hidden p-6 md:p-8 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-8 shrink-0">
        <h3 className="text-[0.6875rem] font-semibold uppercase tracking-[0.08em] text-tx-dim">Siste innlegg</h3>
        <button className="text-[0.6875rem] font-semibold text-accent hover:text-accent-hover transition-colors uppercase tracking-[0.08em] flex items-center gap-1">
          Se alle <ChevronRight className="w-3 h-3" />
        </button>
      </div>

      {/* Posts List - Ingen scroll */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="space-y-8">
          {posts.map((post, idx) => (
            <div key={idx} className="group cursor-pointer">
              {post.featured && post.image && (
                <div className="relative aspect-[16/10] rounded-[1rem] overflow-hidden mb-5 bg-elevated border border-br-subtle">
                  <img
                    src={post.image}
                    alt=""
                    className="w-full h-full object-cover opacity-90 group-hover:opacity-100 group-hover:scale-105 transition-all duration-700"
                  />
                  <div className="absolute top-4 right-4">
                    <span className="bg-accent-subtle text-accent text-[0.6875rem] font-semibold px-3 py-1 rounded-lg tracking-[0.08em] uppercase shadow-xl">
                      {post.category}
                    </span>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-2 mb-2 text-[0.625rem] font-semibold text-tx-dim tracking-[0.06em] uppercase">
                <span>{post.date}</span>
                <span className="opacity-30">•</span>
                <span>{post.category}</span>
              </div>

              <h4 className="text-tx-primary font-bold leading-[1.3] tracking-[-0.01em] group-hover:text-accent transition-colors text-[1.375rem]">
                {post.title}
              </h4>

              {!post.featured && idx < posts.length - 1 && (
                <div className="mt-8 border-b border-br-subtle" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Newsletter Section */}
      <div className="mt-8 pt-8 border-t border-br-default shrink-0">
        <h3 className="text-tx-primary text-[1.0625rem] font-semibold leading-snug mb-3">
          Motta min månedlige oppdatering på boligmarkedet i Oslo.
        </h3>
        <p className="text-tx-muted text-[0.9375rem] font-normal mb-6 leading-relaxed italic opacity-80">
          "Faglig og ærlig om fortid, nåtid og fremtid."
        </p>

        <form onSubmit={handleSubmit} className="relative">
          <div className={`flex items-center border-b transition-all duration-300 pb-2 ${isFocused ? 'border-accent' : 'border-br-default'}`}>
            <input
              type="email"
              required
              placeholder="din e-post"
              value={email}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              onChange={(e) => setEmail(e.target.value)}
              className="bg-transparent border-none outline-none text-tx-primary placeholder:text-tx-dim font-normal text-[0.875rem] w-full py-1"
            />
            <button
              type="submit"
              className="ml-2 p-1.5 text-tx-muted hover:text-tx-primary transition-all transform hover:translate-x-1"
              aria-label="Meld deg på"
            >
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </form>
        <p className="mt-6 text-[0.625rem] text-tx-dim font-semibold uppercase tracking-[0.06em]">Avmeld når som helst</p>
      </div>
    </aside>
  );
};

export default RightPanel;

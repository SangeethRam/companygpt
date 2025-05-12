'use client';

import { usePathname } from 'next/navigation';
import BotUI from '@/components/BotUI';

export default function OverlayPage() {
  const pathname = usePathname(); // e.g., "/www.wikipedia.org/wiki/Morgan_Freeman"
  
  // Ensure the target URL is correctly formed
  const targetUrl = `https://${pathname.slice(1)}`; // transforms into "https://www.wikipedia.org/wiki/Morgan_Freeman"

  return (
    <div className="relative w-full h-screen">
      {/* Embedded page (iframe) */}
      <iframe
        src={targetUrl}
        className="absolute inset-0 w-full h-full"
        style={{
          zIndex: 1, // Make sure iframe stays behind the floating bot
          border: 'none', // Remove iframe border
        }}
        // sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
      />

      {/* Floating Chatbot */}
      <div
        className="bottom-4 right-4 z-50 cursor-pointer"
        style={{
          bottom: '20px',
          right: '20px',
          zIndex: '1000',
          borderRadius: '50%',
          boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.1)',
          backgroundColor: '#00aaff', // Change the background color as per your preference
        }}
      >
        <BotUI />
      </div>
    </div>
  );
}

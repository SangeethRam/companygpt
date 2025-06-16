'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import Draggable, { DraggableEvent, DraggableData } from 'react-draggable';
import { FiMessageSquare, FiMaximize, FiMinimize, FiChevronDown } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type AgentProfile = {
  title: string;
  description: string;
  icon?: string;
  profile?: string;
};

export default function Home() {
  const [open, setOpen] = useState(false);
  const [size, setSize] = useState({ width: 500, height: 400 });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [panelPosition, setPanelPosition] = useState({ x: 100, y: 100 });
  const [messageInput, setMessageInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [profiles, setProfiles] = useState<AgentProfile[]>([]);
  const [profile, setProfile] = useState<AgentProfile | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showInfoPopup, setShowInfoPopup] = useState(false);
  const [chatHistory, setChatHistory] = useState<Record<string, { text: string; isUser: boolean }[]>>({});

  const panelRef = useRef<HTMLDivElement>(null!);
  const botButtonRef = useRef<HTMLButtonElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const infoPopupRef = useRef<HTMLDivElement>(null);

  const currentProfileKey = profile?.title || '';
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const currentMessages = useMemo(() => chatHistory[currentProfileKey] || [], [chatHistory, currentProfileKey]);

  useEffect(() => {
    const fetchProfiles = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/profiles`, { credentials: 'include' });
        const data = await res.json();
        const profilesData: AgentProfile[] = data.profiles || [];
        setProfiles(profilesData);
        if (profilesData.length > 0) {
          const defaultProfile = profilesData[0];
          setProfile(defaultProfile);
          await switchProfile(defaultProfile);
        }
      } catch (err) {
        console.error('Failed to fetch profiles', err);
      }
    };
    fetchProfiles();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentMessages, isThinking]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (infoPopupRef.current && !infoPopupRef.current.contains(e.target as Node)) {
        setShowInfoPopup(false);
      }
    };
    if (showInfoPopup) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showInfoPopup]);

  useEffect(() => {
    const clearSession = async () => {
      try {
        await fetch(`${API_BASE_URL}/clear-session`, {
          method: 'POST',
          credentials: 'include',
        });
      } catch (err) {
        console.error('Error clearing session on refresh', err);
      }
    };
    clearSession();
  }, []);

  useEffect(() => {
    const padding = 20;
    const screenWidth = window.innerWidth;
    const screenHeight = window.innerHeight;
    const panelW = size.width;
    const panelH = size.height;

    const x = Math.min(Math.max(padding, panelPosition.x), screenWidth - panelW - padding);
    const y = Math.min(Math.max(padding, panelPosition.y), screenHeight - panelH - padding);

    setPanelPosition({ x, y });
  }, []);

  const switchProfile = useCallback(async (newProfile: AgentProfile) => {
    if (profile?.title !== newProfile.title) {
      setProfile(newProfile);
      setShowDropdown(false);
      try {
        await fetch(`${API_BASE_URL}/switch-profile/${encodeURIComponent(newProfile.title)}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'user-id': 'EMP001',
          },
          credentials: 'include',
        });
      } catch (err) {
        console.error('Failed to switch profile', err);
      }
      if (!chatHistory[newProfile.title]) {
        setChatHistory((prev) => ({
          ...prev,
          [newProfile.title]: [
            {
              text: `Hello! 👋 I'm the ${newProfile.title} agent. How can I help you today?`,
              isUser: false,
            },
          ],
        }));
      }
    }
  }, [profile?.title, chatHistory]);

  const togglePanel = () => {
    if (open) {
      setOpen(true);
      setIsFullscreen(true);
    } else {
      const panelW = size.width;
      const panelH = size.height;
      const padding = 20;

      const rect = botButtonRef.current?.getBoundingClientRect();
      const x = rect
        ? Math.min(Math.max(padding, rect.left), window.innerWidth - panelW - padding)
        : 100;
      const y = rect
        ? Math.min(Math.max(padding, rect.top - panelH - 10), window.innerHeight - panelH - padding)
        : window.innerHeight - panelH - 100;

      setPanelPosition({ x, y });
      setOpen(true);
      toggleFullscreen()
    }
  };

  const toggleFullscreen = () => {
    const padding = 20;
    const { innerWidth, innerHeight } = window;
    if (isFullscreen) {
      setSize({ width: 500, height: 400 });
    } else {
      setSize({ width: innerWidth - padding * 2, height: innerHeight - padding * 2 });
      setPanelPosition({ x: padding, y: padding });
    }
    setIsFullscreen(!isFullscreen);
  };

  const onDrag = (_e: DraggableEvent, data: DraggableData) => {
    const maxX = window.innerWidth - size.width;
    const maxY = window.innerHeight - size.height;
    const x = Math.min(Math.max(0, data.x), maxX);
    const y = Math.min(Math.max(0, data.y), maxY);
    setPanelPosition({ x, y });
  };

  const handleSendMessage = async () => {
    if (messageInput.trim() === '' || isThinking || !profile) return;
    const userMessage = { text: messageInput, isUser: true };
    setChatHistory((prev) => ({
      ...prev,
      [currentProfileKey]: [...(prev[currentProfileKey] || []), userMessage],
    }));
    setMessageInput('');
    setIsThinking(true);
    try {
      const res = await fetch(`${API_BASE_URL}/ask`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: messageInput }),
      });
      const data = await res.json();
      const botMessage = { text: data.response, isUser: false };
      setChatHistory((prev) => ({
        ...prev,
        [currentProfileKey]: [...(prev[currentProfileKey] || []), botMessage],
      }));
    } catch {
      const errorMessage = { text: '⚠️ Error getting response.', isUser: false };
      setChatHistory((prev) => ({
        ...prev,
        [currentProfileKey]: [...(prev[currentProfileKey] || []), errorMessage],
      }));
    } finally {
      setIsThinking(false);
    }
  };

  return (
    <main className="min-h-screen w-full bg-black text-white font-mono relative overflow-auto">
      {!open && (
        <div className="flex flex-col items-center justify-center h-full p-6">
          <div className="text-4xl md:text-5xl font-bold mb-6 tracking-widest text-white">
            OI_ASSISTANT
          </div>
          <div className="text-center mb-8 max-w-2xl text-sm text-gray-300">
            Welcome to your all-in-one OI assistant.
          </div>

          {/* Agent Feature Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-3xl text-sm mt-4">
            {[
              {
                icon: '🧑‍💼',
                title: 'HR Policy Agent',
                profile: 'HR Assistant',
                description: 'Ask about leave policies, work-from-home rules, and benefits.'
              },
              {
                icon: '📧',
                title: 'Mail Assistant',
                profile: 'Doc Assistant',
                description: 'Draft and send professional emails or meeting invites in seconds.'
              },
              {
                icon: '📄',
                title: 'Doc & PPT Generator',
                profile: 'Doc Assistant',
                description: 'Generate Excel sheets, PowerPoints, or Bonafide certificates instantly.'
              },
              {
                icon: '📅',
                title: 'Calendar Blocker',
                profile: 'IT Help',
                description: 'Block slots, schedule interviews, or set reminders easily.'
              },
              {
                icon: '💻',
                title: 'IT Assistant',
                profile: 'IT Help',
                description: 'Get help with IT issues, ticket creation'}
            ].map((agent, idx) => (
              <div
                key={idx}
                // onClick={() => {
                //   if (!open) togglePanel();
                //   setTimeout(() => {
                //     setProfile(agent)

                //   }, 100);
                //  }} // slight delay to ensure panel is open
                className="group border border-white rounded-lg p-5 bg-zinc-900 hover:bg-green-600 hover:text-black transition-all duration-300 shadow-md hover:shadow-white/30 cursor-pointer"
              >
                <div className="text-3xl mb-3">{agent.icon}</div>
                <h3 className="text-lg font-bold mb-2">{agent.title}</h3>
                <p className="text-gray-300 group-hover:text-black text-sm">{agent.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {!open && (
        <button
          ref={botButtonRef}
          onClick={togglePanel}
          className="fixed bottom-6 right-6 z-[9999] bg-black border border-white hover:bg-green-600 text-white rounded-full p-4 shadow-lg"
        >
          💬
        </button>
      )}

      {open && (
        <Draggable handle=".handle" position={panelPosition} onDrag={onDrag} nodeRef={panelRef}>
          <div
            ref={panelRef}
            style={{ width: size.width, height: size.height }}
            className="fixed z-[9999] bg-white border border-black rounded-md shadow-lg overflow-hidden flex flex-col"

          >
            {/* Header */}
            <div className="handle flex items-center justify-between bg-black text-white px-4 py-2 text-sm relative">
              <div className="flex items-center gap-2 relative">
                {profile && (
                  <button onClick={() => setShowInfoPopup(true)} className="w-7 h-7 rounded-full text-lg bg-white text-black flex items-center justify-center relative">
                    {profile.icon || ''}
                    <span className="absolute top-0 right-0 w-2.5 h-2.5 bg-white rounded-full border border-white" title="Online" />
                  </button>
                )}
                <span className="font-mono">{profile?.title || 'Agent'}</span>
                <button onClick={() => setShowDropdown(!showDropdown)} className="text-white">
                  <FiChevronDown size={16} />
                </button>
                {showDropdown && (
                  <div className="absolute top-full mt-1 left-0 bg-white text-black border rounded shadow-md z-50">
                    {profiles.map((p) => (
                      <div
                        key={p.title}
                        onClick={() => switchProfile(p)}
                        className="px-3 py-1 hover:bg-gray-100 cursor-pointer text-sm flex items-center gap-2"
                      >
                        <span>{p.icon || ''}</span>
                        <span>{p.title}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button onClick={toggleFullscreen} className="bg-black text-white p-1">
                  {isFullscreen ? <FiMinimize size={16} /> : <FiMaximize size={16} />}
                </button>
                <button onClick={() => setOpen(false)} className="bg-black text-white p-1">×</button>
              </div>
            </div>

            {showInfoPopup && profile && (
              <div
                ref={infoPopupRef}
                className="absolute top-16 left-4 bg-white text-black border border-gray-300 rounded shadow-lg p-4 text-xs max-w-sm z-50"
              >
                <div className="flex justify-between items-center mb-2">
                  <p className="font-bold">{profile.title} Agent</p>
                  <button onClick={() => setShowInfoPopup(false)} className="text-black-100 text-xs">×</button>
                </div>
                <p>{profile.description || 'No description available.'}</p>
              </div>
            )}
            

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto text-black p-4 flex flex-col gap-2">
              {currentMessages.map((msg, idx) => (
                 <div
                  key={idx}
                  className={`text-sm px-3 py-2 rounded-lg inline-block ${
                    msg.isUser ? 'bg-blue-100 ml-auto self-end' : 'bg-gray-200 self-start'
                  }`}
                  style={{ maxWidth: '80%', wordBreak: 'break-word' }}
                >
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
                </div>
              ))}
              {isThinking && <div className="text-xs text-gray-500 italic">Thinking...</div>}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Box */}
            <div className="p-2 border-t flex flex-col sm:flex-row items-center gap-2">
              <input
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                className="flex-1 border text-black rounded px-2 py-2 text-sm resize-none w-full"
                placeholder="Type your message and press Enter..."
              />
              <button
                onClick={handleSendMessage}
                disabled={messageInput.trim() === '' || isThinking}
                className="bg-black text-white px-6 py-2 text-sm rounded w-full sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Send
              </button>
            </div>
          </div>
        </Draggable>
      )}
    </main>
  );
}

'use client'

import { useState, useRef, useEffect } from 'react'

type Message = {
  sender: 'user' | 'bot';
  text: string;
};

const policyButtons = [
  { label: 'Dress Code', key: '@dress_code' },
  { label: 'Leave Policy', key: '@leave' },
  { label: 'Annual Leave', key: '@annual_leave' },
  { label: 'Employee Handbook', key: '@employee_handbook' },
  { label: 'Hybrid Work Principles', key: '@hybrid_work' },
  { label: 'Teleworking Policy', key: '@teleworking_policy' },
  { label: 'Teleworking Guidelines', key: '@teleworking_guidelines' },
];

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState<string | null>(null); // Track selected policy
  const bottomRef = useRef<HTMLDivElement>(null);

  const extractPolicyKeys = (text: string): string[] => {
    return policyButtons
      .map((btn) => btn.key)
      .filter((key) => text.includes(key));
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { sender: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    const policyKeys = extractPolicyKeys(userMessage.text);

    try {
      const res = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userMessage.text,
          policyKeys: policyKeys.length > 0 ? policyKeys : undefined,
        }),
      });
      const data = await res.json();
      console.log('Responsee:', data);
      setMessages((prev) => [...prev, { sender: 'bot', text: data }]);
    } catch {
      setMessages((prev) => [...prev, { sender: 'bot', text: '⚠️ Error getting response.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) handleSend();
  };

  const handlePolicyClick = (key: string) => {
    // Toggle selected policy: if it's already selected, unselect it
    if (selectedPolicy === key) {
      setSelectedPolicy(null);
      setInput(input.replace(key, '').trim());
    } else {
      // If a new policy is selected, set it and append to input
      setSelectedPolicy(key);
      setInput((prev) => (prev + ' ' + key).trim());
    }
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <main className="h-screen w-screen bg-gradient-to-br from-gray-100 via-gray-200 to-gray-300 flex items-center justify-center font-sans antialiased">
      <div className="w-full max-w-4xl h-full md:h-[90vh] flex flex-col bg-white/70 backdrop-blur-lg border border-gray-200 rounded-3xl shadow-xl overflow-hidden">
        <header className="p-6 text-center text-2xl font-semibold text-gray-800 border-b border-gray-200">
          💬 Chat Assistant
        </header>

        {/* Policy Buttons */}
        <div className="px-6 py-3 flex flex-wrap gap-2 border-b bg-white/50">
          {policyButtons.map((btn) => (
            <button
              key={btn.key}
              className={`text-sm px-3 py-1 rounded-full transition 
                ${selectedPolicy === btn.key ? 'bg-blue-500 text-white' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'}`}
              onClick={() => handlePolicyClick(btn.key)}
            >
              {btn.label}
            </button>
          ))}
        </div>

        <section className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.sender === 'bot' && (
                <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-base font-bold text-blue-500 mr-3 shadow-sm">
                  🤖
                </div>
              )}
              <div
                className={`px-4 py-3 rounded-2xl text-base max-w-[80%] shadow-md ${
                  msg.sender === 'user'
                    ? 'bg-blue-500 text-white rounded-br-sm'
                    : 'bg-white text-gray-800 border border-gray-200 rounded-bl-sm'
                }`}
              >
                {msg.text}
              </div>
              {msg.sender === 'user' && (
                <div className="w-9 h-9 rounded-full bg-gray-200 flex items-center justify-center text-base font-bold text-gray-700 ml-3 shadow-sm">
                  🧑
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="text-sm text-gray-400 animate-pulse mt-2 ml-12">Bot is thinking...</div>
          )}
          <div ref={bottomRef} />
        </section>

        <footer className="p-5 border-t border-gray-200 bg-white/60 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <input
              className="flex-1 p-3 rounded-full border border-gray-300 bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-400 transition"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-full shadow transition disabled:opacity-50"
              onClick={handleSend}
              disabled={loading}
            >
              Send
            </button>
          </div>
        </footer>
      </div>
    </main>
  );
}

import type { Metadata } from 'next';
import './globals.css';
import { EmojiProvider } from '@/components/EmojiProvider';
import { ToastProvider } from '@/components/Toast';

export const metadata: Metadata = {
  title: 'AAROGYA – AI-Powered Rural Healthcare Companion',
  description: 'AI-driven clinical operations, compliance tracking, and rural health worker alerts management.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
      </head>
      <body className="min-h-screen bg-[#F8FAFC] text-slate-800 antialiased selection:bg-emerald-200 selection:text-slate-900">
        <EmojiProvider>
          <ToastProvider>
            {children}
          </ToastProvider>
        </EmojiProvider>
      </body>
    </html>
  );
}

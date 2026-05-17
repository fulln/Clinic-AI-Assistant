import type { Metadata } from 'next';
import { Manrope } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const manrope = Manrope({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: '诊所 AI 助手平台',
  description: '私立诊所专属 AI 助手',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className={manrope.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

'use client';

import { useEffect } from 'react';
// @ts-ignore
import twemoji from 'twemoji';

const TWEMOJI_CONFIG = {
  callback: (icon: string) =>
    `https://cdn.jsdelivr.net/npm/emoji-datasource-apple/img/apple/64/${icon}.png`,
  attributes: () => ({
    style:
      'width: 1.25em; height: 1.25em; display: inline-block; vertical-align: -0.2em; margin: 0 0.1em; pointer-events: none;',
  }),
};

export function EmojiProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    twemoji.parse(document.body, TWEMOJI_CONFIG);

    const observer = new MutationObserver((mutations) => {
      const hasNewNodes = mutations.some((m) => m.addedNodes.length > 0);
      if (hasNewNodes) {
        observer.disconnect();
        twemoji.parse(document.body, TWEMOJI_CONFIG);
        observer.observe(document.body, { childList: true, subtree: true });
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, []);

  return <>{children}</>;
}

"use client";

import type { ComponentType } from "react";
import { ChefAvatar, type AvatarProviderProps } from "./ChefAvatar";

/**
 * Avatar provider registry. The app talks to an avatar ONLY through `AvatarProviderProps`
 * (phase + live lip level + optional gesture cue), so a realtime avatar vendor can replace the demo avatar
 * without touching the AI, voice or UI code.
 *
 *   NEXT_PUBLIC_AVATAR_PROVIDER=demo      -> DemoAvatar (procedural SVG chef, default)
 *   NEXT_PUBLIC_AVATAR_PROVIDER=external  -> ExternalAvatarProvider (integration point for Tavus / HeyGen / etc.)
 */
export const DemoAvatar: ComponentType<AvatarProviderProps> = ChefAvatar;

/**
 * Integration point for a hosted realtime avatar (Tavus, HeyGen Interactive Avatar, D-ID, Soul Machines ...).
 * Typical implementation: mount the vendor's WebRTC <video>, forward `phase` as the conversation state, and send the
 * assistant's reply text (from useConcierge) to the vendor's "speak" API instead of our own TTS. Until a vendor is
 * wired in, this adapter transparently renders the demo avatar so nothing appears broken.
 */
export const ExternalAvatarProvider: ComponentType<AvatarProviderProps> = function ExternalAvatarProvider(props) {
  return <ChefAvatar {...props} />;
};

const REGISTRY: Record<string, ComponentType<AvatarProviderProps>> = { demo: DemoAvatar, external: ExternalAvatarProvider };

export function getAvatarProvider(name: string): ComponentType<AvatarProviderProps> {
  return REGISTRY[name] ?? DemoAvatar;
}

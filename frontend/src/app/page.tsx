'use client';

import Link from 'next/link';
import { LocaleSwitcher } from '@/shared/components/LocaleSwitcher';
import { useAuthStore } from '@/shared/store/authStore';
import { useLocaleStore } from '@/shared/store/localeStore';
import { getSiteCopy } from '@/shared/i18n/site';

export default function RootPage() {
  const locale = useLocaleStore((state) => state.locale);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const copy = getSiteCopy(locale);

  const cards = [
    { title: copy.landingCardOneTitle, body: copy.landingCardOneBody },
    { title: copy.landingCardTwoTitle, body: copy.landingCardTwoBody },
    { title: copy.landingCardThreeTitle, body: copy.landingCardThreeBody },
    { title: copy.landingCardFourTitle, body: copy.landingCardFourBody },
  ];

  const flow = [
    { title: copy.landingFlowOneTitle, body: copy.landingFlowOneBody },
    { title: copy.landingFlowTwoTitle, body: copy.landingFlowTwoBody },
    { title: copy.landingFlowThreeTitle, body: copy.landingFlowThreeBody },
    { title: copy.landingFlowFourTitle, body: copy.landingFlowFourBody },
  ];

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="saas-panel px-6 py-5 sm:px-8">
          <div className="mb-2 flex justify-end">
            <LocaleSwitcher className="w-32" compact hideLabel />
          </div>
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <span className="saas-pill">{copy.landingEyebrow}</span>
              <h1 className="mt-5 max-w-3xl text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
                {copy.landingTitle}
              </h1>
              <p className="mt-5 max-w-3xl text-base leading-8 text-slate-500">
                {copy.landingBody}
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              {!isAuthenticated && (
                <Link
                  href="/login"
                  className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-[0_16px_32px_rgba(15,23,42,0.16)] transition hover:bg-slate-800"
                >
                  {copy.landingPrimaryCta}
                </Link>
              )}
              <Link
                href="/conversation"
                className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
              >
                {copy.landingSecondaryCta}
              </Link>
            </div>
          </div>
        </header>

        <section className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {cards.map((card, index) => (
            <article key={card.title} className="saas-panel p-6">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-sm font-bold text-white">
                0{index + 1}
              </div>
              <h2 className="text-lg font-semibold text-slate-900">{card.title}</h2>
              <p className="mt-3 text-sm leading-7 text-slate-500">{card.body}</p>
            </article>
          ))}
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="saas-panel p-6 sm:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
              {copy.landingFlowTitle}
            </p>
            <div className="mt-6 space-y-5">
              {flow.map((item) => (
                <div key={item.title} className="rounded-2xl border border-slate-200/80 bg-slate-50/75 px-4 py-4">
                  <h3 className="text-base font-semibold text-slate-900">{item.title}</h3>
                  <p className="mt-2 text-sm leading-7 text-slate-500">{item.body}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="saas-panel overflow-hidden p-6 sm:p-8">
            <div className="rounded-[1.5rem] border border-slate-200 bg-slate-950 p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                    {copy.appName}
                  </p>
                  <h2 className="mt-3 text-2xl font-semibold">{copy.dashboardOverview}</h2>
                </div>
                <span className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-3 py-1 text-xs font-semibold text-emerald-300">
                  {copy.dashboardWorkspaceHealthy}
                </span>
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-400">{copy.navConversation}</p>
                  <p className="mt-3 text-sm leading-6 text-slate-300">{copy.dashboardSubtitleConversation}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-400">{copy.navAgents}</p>
                  <p className="mt-3 text-sm leading-6 text-slate-300">{copy.dashboardSubtitleAgents}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-400">{copy.navKnowledgeBase}</p>
                  <p className="mt-3 text-sm leading-6 text-slate-300">{copy.dashboardSubtitleKnowledgeBase}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-400">{copy.navAgentManagement}</p>
                  <p className="mt-3 text-sm leading-6 text-slate-300">{copy.dashboardSubtitleAgentManagement}</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

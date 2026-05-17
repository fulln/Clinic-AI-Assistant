'use client';

import { LoginForm } from '@/features/auth/components/LoginForm';
import { useLocaleStore } from '@/shared/store/localeStore';
import { getSiteCopy } from '@/shared/i18n/site';

export default function LoginPage() {
  const locale = useLocaleStore((state) => state.locale);
  const copy = getSiteCopy(locale);

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-10 sm:px-6 lg:px-8">
      <div className="grid w-full max-w-6xl overflow-hidden rounded-[2rem] border border-white/70 bg-white/82 shadow-[0_30px_120px_rgba(15,23,42,0.12)] backdrop-blur-xl lg:grid-cols-[1.1fr_0.9fr]">
        <section className="relative hidden overflow-hidden bg-slate-950 px-10 py-12 text-white lg:flex lg:flex-col">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(96,165,250,0.34),transparent_36%),radial-gradient(circle_at_bottom_right,rgba(34,197,94,0.18),transparent_30%)]" />
          <div className="relative flex-1">
            <span className="saas-pill border-white/15 bg-white/10 text-slate-200">
              {copy.authMarketingEyebrow}
            </span>
            <h1 className="mt-8 max-w-xl text-4xl font-semibold leading-tight">
              {copy.authMarketingTitle}
            </h1>
            <p className="mt-5 max-w-lg text-base leading-7 text-slate-300">
              {copy.authMarketingBody}
            </p>
          </div>

          <div className="relative grid gap-4">
            {[copy.authFeatureOne, copy.authFeatureTwo, copy.authFeatureThree].map((feature) => (
              <div
                key={feature}
                className="rounded-2xl border border-white/10 bg-white/6 px-4 py-4 text-sm text-slate-200"
              >
                <div className="mb-2 h-2 w-2 rounded-full bg-cyan-300" />
                {feature}
              </div>
            ))}
          </div>
        </section>

        <section className="flex items-center justify-center px-6 py-10 sm:px-10">
          <div className="w-full max-w-md">
            <div className="saas-pill mb-6 w-fit">
              {copy.appName}
            </div>
            <div className="mb-8">
              <h2 className="text-3xl font-semibold tracking-tight text-slate-900">
                {copy.authLoginTitle}
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">{copy.authLoginSubtitle}</p>
            </div>
            <LoginForm />
          </div>
        </section>
      </div>
    </div>
  );
}

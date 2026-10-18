import type { ArmPose, Pose } from "./pose";

/**
 * AURA - waist-up chef concierge, drawn as layered SVG so every part (arms, hands, eyes, brows, mouth) can be driven
 * by the animation engine in ChefAvatar.tsx. Coordinate space: 600 x 760 (head at top, cropped at the hips).
 */
export const VIEWBOX = "0 0 600 760";
const SKIN = "#D2976C";
const SKIN_SHADE = "#B97D55";
const SKIN_LIGHT = "#E3AF86";
const WHITE = "#FBF9F5";
const WHITE_SHADE = "#E6E0D5";
const LINE = "#CFC8BA";
const HAIR = "#1B1311";
const GOLD = "#D9AE5B";
const SHOULDER = { x: 212, y: 392 };
const UA = 135;
const FA = 120;

const f = (n: number) => Math.round(n * 100) / 100;

function Hand({ arm }: { arm: ArmPose }) {
  const tips = [27, 31, 28, 22];
  return (
    <g transform="scale(1.22)">
      <rect x={-12} y={-8} width={24} height={16} rx={7} fill={SKIN_SHADE} />
      {/* thumb (outward side when the arm hangs down) */}
      <g transform={`translate(-17 14) rotate(${f(30 + (1 - arm.fingers[0]) * 18 + arm.spread * 0.8)})`}>
        <rect x={-5.2} y={-2} width={10.4} height={f(Math.max(10, 25 * arm.fingers[0]))} rx={5.2} fill={SKIN} stroke={SKIN_SHADE} strokeWidth={0.8} />
      </g>
      {tips.map((len, i) => {
        const ext = arm.fingers[i + 1];
        return (
          <g key={i} transform={`translate(${-13.5 + i * 9} 36) rotate(${f(((1.5 - i) * arm.spread) / 1.5)})`}>
            <rect x={-4.6} y={-4} width={9.2} height={f(Math.max(9, len * ext + 4))} rx={4.6} fill={SKIN} stroke={SKIN_SHADE} strokeWidth={0.8} />
          </g>
        );
      })}
      <rect x={-19} y={0} width={38} height={42} rx={15} fill={SKIN} stroke={SKIN_SHADE} strokeWidth={0.8} />
      <path d="M-9 12 Q0 20 9 12" stroke={SKIN_SHADE} strokeWidth={1.2} fill="none" opacity={0.5} />
    </g>
  );
}

function Arm({ arm }: { arm: ArmPose }) {
  return (
    <g transform={`translate(${SHOULDER.x} ${SHOULDER.y}) rotate(${f(arm.sh)})`}>
      {/* upper arm sleeve */}
      <rect x={-31} y={-18} width={62} height={UA + 26} rx={28} fill={WHITE} stroke={LINE} strokeWidth={1.5} />
      <g transform={`translate(0 ${UA}) rotate(${f(arm.el)})`}>
        <rect x={-26} y={-14} width={52} height={FA + 14} rx={22} fill={WHITE} stroke={LINE} strokeWidth={1.5} />
        <path d={`M-26 ${FA - 22} Q0 ${FA - 14} 26 ${FA - 22}`} stroke={WHITE_SHADE} strokeWidth={2} fill="none" />
        <rect x={-28} y={FA - 16} width={56} height={16} rx={8} fill={WHITE} stroke={LINE} strokeWidth={1.5} />
        <g transform={`translate(0 ${FA - 2}) rotate(${f(arm.wr)})`}>
          <Hand arm={arm} />
        </g>
      </g>
      <circle cx={0} cy={0} r={30} fill={WHITE} />
    </g>
  );
}

function mouthShapes(open: number, wide: number, smile: number) {
  const o = Math.max(0, Math.min(1, open));
  const cx = 300;
  const cy = 286;
  const hw = 17 + 6 * wide - 5 * o * (1 - wide);
  const cornerY = cy - 2.2 * smile;
  const L = `${f(cx - hw)},${f(cornerY)}`;
  const R = `${f(cx + hw)},${f(cornerY)}`;
  const lowerInner = cy + 3 + 30 * o;
  const lowerOuter = cy + 12 + 33 * o;
  return {
    cx, cy, hw, o,
    inner: `M${L} Q${cx},${f(cy - 2)} ${R} Q${cx},${f(lowerInner)} ${L} Z`,
    upperLip: `M${L} Q${f(cx - hw / 2)},${f(cy - 9)} ${cx},${f(cy - 6)} Q${f(cx + hw / 2)},${f(cy - 9)} ${R} Q${cx},${f(cy - 3)} ${L} Z`,
    lowerLip: `M${L} Q${cx},${f(lowerInner + 0.5)} ${R} Q${cx},${f(lowerOuter)} ${L} Z`,
    teethH: 3 + 9 * o,
    tongueY: cy + 8 + 15 * o,
  };
}

function Eye({ cx, side, gaze, blink }: { cx: number; side: "l" | "r"; gaze: Pose["gaze"]; blink: number }) {
  const cy = 230;
  const lid = Math.max(blink, 0.1);
  const id = `av-eye-${side}`;
  return (
    <g>
      <clipPath id={id}>
        <ellipse cx={cx} cy={cy} rx={15} ry={10} />
      </clipPath>
      <ellipse cx={cx} cy={cy} rx={15.5} ry={10.5} fill={SKIN_SHADE} opacity={0.35} />
      <g clipPath={`url(#${id})`}>
        <ellipse cx={cx} cy={cy} rx={15} ry={10} fill="#FBF7F2" />
        <circle cx={f(cx + gaze.x * 6)} cy={f(cy + gaze.y * 3.6)} r={7.6} fill="#4B2E1F" />
        <circle cx={f(cx + gaze.x * 6)} cy={f(cy + gaze.y * 3.6)} r={3.7} fill="#120A07" />
        <circle cx={f(cx + gaze.x * 6 - 2.4)} cy={f(cy + gaze.y * 3.6 - 2.8)} r={1.7} fill="#fff" opacity={0.9} />
        <rect x={cx - 17} y={cy - 12} width={34} height={f(22 * lid)} fill={SKIN} />
      </g>
      <path d={`M${cx - 15.5} ${f(cy - 10 + 22 * lid)} Q${cx} ${f(cy - 14 + 24 * lid)} ${cx + 15.5} ${f(cy - 10 + 22 * lid)}`} stroke={HAIR} strokeWidth={2.6} fill="none" strokeLinecap="round" />
    </g>
  );
}

export function AvatarSvg({ pose, idPrefix = "av" }: { pose: Pose; idPrefix?: string }) {
  const m = mouthShapes(pose.mouth.open, pose.mouth.wide, pose.mouth.smile);
  const browY = (lift: number) => 207 - lift * 8;
  const bw = pose.brow.furrow;
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox={VIEWBOX} role="img" aria-label="AURA, the digital dining concierge" style={{ width: "100%", height: "100%" }}>
      <defs>
        <linearGradient id={`${idPrefix}-skin`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={SKIN_LIGHT} />
          <stop offset="1" stopColor={SKIN} />
        </linearGradient>
        <linearGradient id={`${idPrefix}-jacket`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#EFEAE0" />
          <stop offset="0.5" stopColor={WHITE} />
          <stop offset="1" stopColor="#EDE7DC" />
        </linearGradient>
        <radialGradient id={`${idPrefix}-hat`} cx="0.5" cy="0.35" r="0.7">
          <stop offset="0" stopColor="#FFFFFF" />
          <stop offset="1" stopColor="#EAE4D9" />
        </radialGradient>
        <clipPath id={`${idPrefix}-mouth`}>
          <path d={m.inner} />
        </clipPath>
      </defs>

      {/* torso (breathes) */}
      <g transform={`translate(0 ${f(pose.breath * -1.2)})`}>
        <path d="M178 404 Q178 372 214 366 L386 366 Q422 372 422 404 L430 760 L170 760 Z" fill={`url(#${idPrefix}-jacket)`} stroke={LINE} strokeWidth={1.5} />
        <rect x={298} y={420} width={124} height={340} fill="#F7F4EE" opacity={0.55} />
        <path d="M298 420 L298 760" stroke={LINE} strokeWidth={1.6} />
        {[480, 540, 600, 660, 720].map((y) => (
          <g key={y}>
            <circle cx={338} cy={y} r={8.5} fill={GOLD} stroke="#B98F3E" strokeWidth={1.4} />
            <circle cx={338} cy={y} r={3} fill="#B98F3E" opacity={0.55} />
            <circle cx={262} cy={y} r={8.5} fill={GOLD} stroke="#B98F3E" strokeWidth={1.4} />
            <circle cx={262} cy={y} r={3} fill="#B98F3E" opacity={0.55} />
          </g>
        ))}
        <text x={222} y={462} fontSize={15} fontFamily="Georgia, serif" fill={GOLD} letterSpacing={2.5} textAnchor="middle" fontStyle="italic">AURA</text>
        {/* neck + collar */}
        <path d="M272 318 L328 318 L332 372 Q300 390 268 372 Z" fill={SKIN_SHADE} />
        <path d="M262 352 L300 424 L240 440 L228 380 Q242 358 262 352 Z" fill={WHITE} stroke={LINE} strokeWidth={1.5} />
        <path d="M338 352 L300 424 L360 440 L372 380 Q358 358 338 352 Z" fill={WHITE} stroke={LINE} strokeWidth={1.5} />
        <path d="M266 356 L300 420" stroke={GOLD} strokeWidth={2} opacity={0.8} />
        <path d="M334 356 L300 420" stroke={GOLD} strokeWidth={2} opacity={0.8} />
        {/* saffron neckerchief */}
        <path d="M270 364 Q300 384 330 364 L318 394 Q300 414 282 394 Z" fill="#E27B3B" stroke="#C5622A" strokeWidth={1.2} />
        <circle cx={300} cy={396} r={7} fill="#C5622A" />
      </g>

      {/* head */}
      <g transform={`translate(${f(pose.head.tx)} ${f(pose.head.ty)}) rotate(${f(pose.head.rot)} 300 330)`}>
        <ellipse cx={300} cy={208} rx={74} ry={86} fill={HAIR} />
        <ellipse cx={234} cy={242} rx={12} ry={16} fill={SKIN_SHADE} />
        <ellipse cx={366} cy={242} rx={12} ry={16} fill={SKIN_SHADE} />
        <ellipse cx={300} cy={236} rx={66} ry={80} fill={`url(#${idPrefix}-skin)`} />
        <path d="M244 262 Q300 330 356 262 L356 280 Q300 346 244 280 Z" fill={SKIN_SHADE} opacity={0.18} />
        <ellipse cx={262} cy={262} rx={15} ry={9} fill="#D9715F" opacity={0.2} />
        <ellipse cx={338} cy={262} rx={15} ry={9} fill="#D9715F" opacity={0.2} />
        {/* fringe under the hat */}
        <path d="M234 206 C238 164 362 164 366 206 C352 186 330 176 300 176 C270 176 248 186 234 206 Z" fill={HAIR} />

        <Eye cx={272} side="l" gaze={pose.gaze} blink={pose.blink} />
        <Eye cx={328} side="r" gaze={pose.gaze} blink={pose.blink} />
        <path d={`M${254 + bw * 4} ${f(browY(pose.brow.l) + bw * 3)} Q272 ${f(browY(pose.brow.l) - 8)} 291 ${f(browY(pose.brow.l) + 2 - bw * 2)}`} stroke={HAIR} strokeWidth={5} strokeLinecap="round" fill="none" />
        <path d={`M${346 - bw * 4} ${f(browY(pose.brow.r) + bw * 3)} Q328 ${f(browY(pose.brow.r) - 8)} 309 ${f(browY(pose.brow.r) + 2 - bw * 2)}`} stroke={HAIR} strokeWidth={5} strokeLinecap="round" fill="none" />
        <path d="M297 236 Q292 258 288 262 Q300 270 312 262 Q308 258 303 236" fill="none" stroke={SKIN_SHADE} strokeWidth={2} strokeLinecap="round" opacity={0.7} />

        {/* mouth */}
        <path d={m.inner} fill="#4A1818" />
        <g clipPath={`url(#${idPrefix}-mouth)`}>
          {m.o > 0.1 && <rect x={m.cx - m.hw} y={m.cy - 4} width={m.hw * 2} height={f(m.teethH)} rx={3} fill="#FFFFFF" />}
          {m.o > 0.18 && <ellipse cx={m.cx} cy={f(m.tongueY)} rx={f(9 + 3 * m.o)} ry={f(4 + 7 * m.o)} fill="#C4636A" />}
        </g>
        <path d={m.upperLip} fill="#B5524F" />
        <path d={m.lowerLip} fill="#C4635E" />

        {/* chef hat (toque) */}
        <g>
          <circle cx={248} cy={96} r={40} fill={`url(#${idPrefix}-hat)`} stroke={LINE} strokeWidth={1.4} />
          <circle cx={352} cy={96} r={40} fill={`url(#${idPrefix}-hat)`} stroke={LINE} strokeWidth={1.4} />
          <circle cx={300} cy={66} r={48} fill={`url(#${idPrefix}-hat)`} stroke={LINE} strokeWidth={1.4} />
          <circle cx={268} cy={50} r={32} fill={`url(#${idPrefix}-hat)`} stroke={LINE} strokeWidth={1.2} />
          <circle cx={334} cy={48} r={32} fill={`url(#${idPrefix}-hat)`} stroke={LINE} strokeWidth={1.2} />
          <rect x={226} y={96} width={148} height={42} fill={`url(#${idPrefix}-hat)`} />
          <rect x={228} y={124} width={144} height={44} rx={9} fill={WHITE} stroke={LINE} strokeWidth={1.5} />
          {[252, 276, 300, 324, 348].map((x) => (<path key={x} d={`M${x} 128 L${x} 164`} stroke={WHITE_SHADE} strokeWidth={2} />))}
          <path d="M228 160 Q300 170 372 160" stroke={GOLD} strokeWidth={2.4} fill="none" opacity={0.85} />
        </g>
      </g>

      {/* arms are drawn last so raised hands sit in front of the body */}
      <Arm arm={pose.armL} />
      <g transform="translate(600 0) scale(-1 1)">
        <Arm arm={pose.armR} />
      </g>
    </svg>
  );
}

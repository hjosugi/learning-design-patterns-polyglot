export const strategies = {
  none: (cents) => cents,
  seasonal: (cents) => Math.round(cents * 0.9),
  vip: (cents) => Math.round(cents * 0.8),
};

export function checkout(totalCents, strategy) {
  if (totalCents < 0) {
    throw new Error("total must be positive");
  }
  return strategy(totalCents);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  for (const [name, strategy] of Object.entries(strategies)) {
    console.log(`${name}: ${checkout(12_500, strategy)}`);
  }
}

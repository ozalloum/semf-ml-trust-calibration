# Paper 3 novelty positioning - final pre-data version

## Claims that are already established in the literature
The final paper will not claim novelty for:
- using ML to improve nuclear-mass predictions;
- residual/model repair;
- physics-informed features such as magic-number distance or pairing;
- historical AME extrapolation by itself;
- local/model weighting by itself;
- shell corrections to semi-empirical mass formulas;
- achieving state-of-the-art nuclear-mass RMSE.

## Distinct contribution tested by the frozen protocol
The paper's distinctive question is:

> How much should machine learning trust an approximate, interpretable nuclear-physics prior when that prior is deliberately or naturally misspecified?

The study makes trust conditional on the joint axes
`prior fidelity x integration mechanism x nuclear-chart region x extrapolation difficulty x observable x coefficient uncertainty/calibration drift`.

The primary physics prior is intentionally simple because it is interpretable and perturbable. A shell-aware BWN control tests whether the conclusion is merely an artifact of choosing a weak liquid-drop prior.

## Strongest potential contribution
The strongest possible result, if the empirical data support it, is **observable-dependent physics trust**: the same physics prior and same nuclei can show G>1 for a bulk binding endpoint while G<1 for a shell-sensitive endpoint, or vice versa.

That finding would mean that 'physics accuracy' is not a single scalar property of a prior. It depends on what physical observable the prediction is being asked to preserve.

## Claim discipline
Even if results are strong, the manuscript will avoid universal trust thresholds, claims of fundamental-constant extraction, claims that magic nuclei necessarily maximize SEMF total-mass error, and prospective language for post-AME2020 formula forms.

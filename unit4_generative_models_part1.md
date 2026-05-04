# Unit 4: Generative Models — Questions 1–5

---

## Q1. Explain the architecture of an autoencoder and its role in dimensionality reduction. (L2–L3)

### Definition

An **autoencoder (AE)** is an unsupervised neural network trained to learn a compressed, low-dimensional representation (encoding) of input data and then reconstruct the original input from that representation. It learns the identity function under constraints.

### Architecture

An autoencoder consists of three main components:

```
Input (x) → [Encoder] → Latent Code (z) → [Decoder] → Reconstructed Output (x̂)
```

#### 1. Encoder Network
- Maps input **x ∈ ℝⁿ** to a lower-dimensional latent representation **z ∈ ℝᵈ** (where d ≪ n).
- Consists of one or more hidden layers with progressively fewer neurons.
- Mathematically: **z = f_θ(x) = σ(Wx + b)**, where σ is an activation function (ReLU, sigmoid).
- The encoder *compresses* the data, forcing the network to learn only the most salient features.

#### 2. Bottleneck (Latent Space)
- The narrowest layer of the network, representing the **compressed code**.
- Its dimensionality `d` is a hyperparameter that controls the degree of compression.
- This layer holds the learned representation — the "essence" of the input data.

#### 3. Decoder Network
- Maps the latent code **z** back to the original input space, producing **x̂ ∈ ℝⁿ**.
- Mirrors the encoder architecture (symmetric layers with increasing neurons).
- Mathematically: **x̂ = g_φ(z) = σ'(W'z + b')**.

### Loss Function

The network is trained by minimizing **reconstruction error**:

- **MSE Loss**: L(x, x̂) = ||x − x̂||²
- **Binary Cross-Entropy** (for normalized inputs): L = −Σ[xᵢ log(x̂ᵢ) + (1−xᵢ) log(1−x̂ᵢ)]

### Role in Dimensionality Reduction

| Aspect | Explanation |
|--------|-------------|
| **Feature Compression** | The bottleneck forces the network to learn a compact representation, discarding noise and redundancy. |
| **Non-linear Mapping** | Unlike PCA (linear), autoencoders capture **non-linear relationships** in the data through activation functions. |
| **Data Manifold Learning** | The latent space captures the underlying manifold structure of high-dimensional data. |
| **Denoising** | Denoising autoencoders learn robust features by reconstructing clean data from corrupted inputs. |
| **Visualization** | Reducing data to 2D/3D latent spaces enables visualization of clusters and patterns. |

### Types of Autoencoders

- **Undercomplete AE**: Bottleneck dimension < input dimension (standard dimensionality reduction).
- **Sparse AE**: Adds sparsity penalty to encourage learning useful features even with overcomplete representations.
- **Denoising AE**: Trained to reconstruct original data from noisy inputs.
- **Contractive AE**: Adds penalty on the Frobenius norm of the Jacobian of the encoder, making the learned representation robust to small input perturbations.

### Diagram

```
Input Layer    Encoder Layers    Bottleneck    Decoder Layers    Output Layer
[784] ——→ [512] ——→ [256] ——→ [32] ——→ [256] ——→ [512] ——→ [784]
  x                              z                               x̂
```

> The autoencoder achieves dimensionality reduction by learning to represent high-dimensional data in a compact latent space while preserving the information necessary for accurate reconstruction.

---

## Q2. Analyse how autoencoders perform feature extraction compared to traditional methods like PCA. (L4)

### Overview

Both autoencoders and PCA aim to learn compact representations of data, but they differ fundamentally in their approach, capacity, and applicability.

### PCA (Principal Component Analysis)

- A **linear** dimensionality reduction technique.
- Finds orthogonal directions (principal components) that maximize variance.
- Mathematically: projects data onto eigenvectors of the covariance matrix.
- Solution: **z = Wᵀx**, where W contains the top-k eigenvectors.
- Reconstruction: **x̂ = Wz**.

### Autoencoders for Feature Extraction

- Learn a **non-linear** mapping from input to latent space.
- Use neural networks with non-linear activations (ReLU, sigmoid, tanh).
- Can capture complex, hierarchical features.
- Encoder: **z = f(x)**, Decoder: **x̂ = g(z)** where f, g are neural networks.

### Comparative Analysis

| Criterion | PCA | Autoencoder |
|-----------|-----|-------------|
| **Mapping Type** | Linear transformation | Non-linear transformation |
| **Feature Type** | Linear combinations of input features | Hierarchical, abstract features |
| **Expressiveness** | Limited to linear subspaces | Can model complex manifolds |
| **Computational Cost** | Efficient (eigenvalue decomposition) | Expensive (gradient-based training) |
| **Interpretability** | High (eigenvectors have clear meaning) | Low (latent dimensions are abstract) |
| **Scalability** | Struggles with very high-dimensional data | Scales well with GPU acceleration |
| **Overfitting Risk** | No risk (closed-form solution) | Requires regularization |
| **Data Requirement** | Works with small datasets | Requires large datasets for deep models |
| **Optimality** | Globally optimal for linear case | May converge to local minima |

### Key Analytical Points

**1. Linear AE ≈ PCA:**
A single-layer autoencoder with linear activations and MSE loss learns the same subspace as PCA. The latent representations span the same principal subspace, though the basis vectors may differ by rotation.

**2. Non-linear Advantage:**
Deep autoencoders with non-linear activations capture features PCA cannot:
- Curved manifolds (e.g., Swiss roll dataset)
- Hierarchical features in images (edges → textures → objects)
- Complex dependencies in sequential data

**3. Feature Quality:**
- PCA features are **globally optimal** for linear reconstruction.
- AE features are **task-adaptable** — can be fine-tuned for downstream tasks like classification.
- Sparse autoencoders learn **disentangled features** that are individually meaningful.

**4. Reconstruction Quality:**
For the same latent dimensionality, deep autoencoders typically achieve **lower reconstruction error** on complex datasets (images, audio) because they model non-linear structure.

**5. Example — MNIST Digits:**
- PCA with 30 components: Blurry reconstructions, ~95% variance captured.
- AE with 30-dim bottleneck: Sharper reconstructions, captures digit-specific features.

### When to Use Each

- **PCA**: Small datasets, need for interpretability, data is approximately linear, quick baseline.
- **Autoencoders**: Large complex datasets, non-linear relationships, pre-training for deep networks, image/audio data.

> In summary, autoencoders subsume and extend PCA's capabilities by learning non-linear feature extractors, but at the cost of increased computational complexity and reduced interpretability.

---

## Q3. Explain the concept of Variational Autoencoders (VAEs) and the role of the reparameterization trick. (L3–L4)

### Concept of VAEs

A **Variational Autoencoder (VAE)** is a generative model that combines deep learning with Bayesian inference. Unlike standard autoencoders that map inputs to fixed points in latent space, VAEs map inputs to **probability distributions** over the latent space.

### Architecture

```
Input (x) → Encoder → [μ, σ²] → Sampling (z) → Decoder → Reconstructed Output (x̂)
```

#### Encoder (Recognition/Inference Network)
- Outputs **two vectors**: mean **μ** and log-variance **log σ²** of a Gaussian distribution.
- Defines the approximate posterior: **q_φ(z|x) = N(z; μ, σ²I)**.

#### Latent Sampling
- Sample **z ~ N(μ, σ²I)** from the learned distribution.
- This introduces stochasticity, making the latent space continuous and smooth.

#### Decoder (Generative Network)
- Takes sampled **z** and reconstructs **x̂**.
- Defines the likelihood: **p_θ(x|z)**.

### Loss Function (ELBO)

VAEs maximize the **Evidence Lower Bound (ELBO)**:

```
L(θ, φ; x) = E_q[log p_θ(x|z)] − D_KL(q_φ(z|x) || p(z))
```

| Term | Role |
|------|------|
| **Reconstruction Loss** E_q[log p_θ(x\|z)] | Ensures decoded output matches input (MSE or BCE) |
| **KL Divergence** D_KL(q_φ(z\|x) \|\| p(z)) | Regularizes the latent space to follow N(0, I), ensuring smooth interpolation |

The KL divergence has a **closed-form solution** for Gaussians:
```
D_KL = −½ Σ(1 + log σ² − μ² − σ²)
```

### The Reparameterization Trick

#### The Problem
- Sampling **z ~ N(μ, σ²)** is a **stochastic** operation.
- Gradients cannot flow through random sampling nodes during backpropagation.
- This makes the model **non-differentiable** and untrainable with standard gradient descent.

#### The Solution
Reparameterize the sampling as a **deterministic function** of the parameters plus external noise:

```
z = μ + σ ⊙ ε,    where ε ~ N(0, I)
```

- **ε** is sampled from a fixed distribution (independent of model parameters).
- **μ** and **σ** are deterministic outputs of the encoder.
- The ⊙ denotes element-wise multiplication.

#### Why It Works

| Without Trick | With Trick |
|---------------|------------|
| z is sampled directly → stochastic node | z = μ + σ·ε → deterministic transformation |
| Gradients blocked at sampling | Gradients flow through μ and σ |
| Cannot use backpropagation | Standard backpropagation applies |

The randomness is "externalized" to ε, which doesn't depend on learnable parameters. This allows:
- ∂L/∂μ and ∂L/∂σ to be computed via chain rule.
- End-to-end training with SGD/Adam optimizers.

#### Diagram

```
Without reparameterization:       With reparameterization:
μ, σ → [Sample z ~ N(μ,σ)] → z   μ, σ, ε~N(0,1) → [z = μ + σ·ε] → z
         ✗ (no gradient)                    ✓ (gradient flows)
```

### Properties of VAE Latent Space

- **Continuity**: Nearby points in latent space produce similar outputs.
- **Completeness**: Every point in latent space produces meaningful output.
- **Smooth Interpolation**: Interpolating between two latent codes generates smooth transitions.

> The reparameterization trick is the key innovation that makes VAEs trainable, by converting a stochastic sampling operation into a differentiable deterministic computation, enabling gradient-based optimization of the variational objective.

---

## Q4. Compare autoencoders and VAEs in terms of generative capability and output quality. (L4)

### Fundamental Difference

| Aspect | Autoencoder (AE) | Variational Autoencoder (VAE) |
|--------|-------------------|-------------------------------|
| **Nature** | Deterministic model | Probabilistic generative model |
| **Latent Space** | Unstructured point embeddings | Structured probability distributions |
| **Objective** | Minimize reconstruction error | Maximize ELBO (reconstruction + KL) |
| **Primary Use** | Compression, denoising | Generation, interpolation |

### Generative Capability Analysis

#### Standard Autoencoders — Limited Generation

1. **No principled sampling**: The latent space has no imposed structure. Random sampling from this space produces **meaningless or distorted outputs**.
2. **Discontinuous latent space**: Gaps and irregularities exist between encoded data points. Sampling from gaps yields garbage.
3. **Overfitting to training data**: The encoder maps each input to a specific point — no probability model exists to generate new points.
4. **No density estimation**: AEs cannot estimate p(x) or p(z), making principled generation impossible.

#### VAEs — Designed for Generation

1. **Structured latent space**: The KL divergence term forces q(z|x) towards N(0, I), creating a smooth, regular latent space.
2. **Principled sampling**: New data is generated by sampling z ~ N(0, I) and decoding: x_new = Decoder(z).
3. **Interpolation**: Smooth transitions between data points by linearly interpolating latent vectors.
4. **Density estimation**: VAEs approximate p(x) = ∫ p(x|z)p(z)dz, providing a probabilistic model of the data.

### Output Quality Comparison

| Quality Metric | AE | VAE |
|----------------|-----|-----|
| **Reconstruction Fidelity** | ✅ High (sole objective) | ⚠️ Lower (trade-off with KL term) |
| **Sharpness** | Sharp reconstructions | Tends to produce **blurry** outputs |
| **Diversity of Generations** | Poor (cannot generate) | Good (samples diverse outputs) |
| **Semantic Smoothness** | No guarantee | Smooth latent interpolation |
| **Novel Sample Quality** | ✗ Cannot generate novel samples | ✓ Generates plausible new samples |

### Why VAE Outputs Are Blurry

1. **KL-Reconstruction Trade-off**: The KL term pushes latent distributions to overlap, reducing the model's ability to encode fine details.
2. **Gaussian Assumption**: Modeling p(x|z) as Gaussian with MSE loss averages over modes, producing blurry reconstructions.
3. **Posterior Collapse**: In some cases, the decoder ignores z entirely, producing generic outputs.

### Practical Comparison

**Task: Face Generation (CelebA dataset)**
- **AE**: Can reconstruct training faces well but cannot generate new faces. Sampling random z produces noise-like images.
- **VAE**: Generates novel, plausible faces. Supports attribute manipulation (adding smile, changing hair). However, faces appear slightly blurry compared to real images.

### Improvements to VAE Quality

- **β-VAE**: Adjusts weight of KL term to balance disentanglement and reconstruction.
- **VQ-VAE**: Uses discrete latent codes, producing sharper outputs.
- **VAE-GAN Hybrid**: Combines VAE's structured latent space with GAN's discriminator for sharper outputs.

> In conclusion, standard AEs excel at reconstruction but lack generative capability, while VAEs sacrifice some reconstruction fidelity to gain a structured, continuous latent space that enables principled data generation. VAEs are true generative models; AEs are not.

---

## Q5. Explain the architecture and working of Generative Adversarial Networks (GANs). (L3)

### Definition

A **Generative Adversarial Network (GAN)** is a generative model consisting of two neural networks — a **Generator (G)** and a **Discriminator (D)** — that are trained simultaneously in a **minimax game**. Proposed by Ian Goodfellow et al. (2014).

### Architecture

```
Random Noise z ~ N(0,1) → [Generator G] → Fake Image (G(z))
                                                ↓
Real Data x ────────────────────────→ [Discriminator D] → Real/Fake (probability)
                                                ↑
                                          Fake Image (G(z))
```

#### 1. Generator Network (G)

- **Input**: Random noise vector **z ~ p_z(z)** (typically N(0, I)), dimension ~100.
- **Output**: Synthetic data sample **G(z)** in the same space as real data.
- **Architecture** (for image generation):
  - Fully connected layer to project z into a spatial tensor.
  - Series of **transposed convolutional layers** (upsampling).
  - Batch normalization after each layer (except output).
  - **ReLU** activations in hidden layers, **Tanh** in output layer.
- **Goal**: Generate data indistinguishable from real data to fool D.

#### 2. Discriminator Network (D)

- **Input**: Either real data **x** or generated data **G(z)**.
- **Output**: Probability **D(x)** that the input is real (scalar in [0, 1]).
- **Architecture**:
  - Series of **convolutional layers** (downsampling) with stride 2.
  - **LeakyReLU** activations (slope 0.2).
  - No batch normalization in the first layer.
  - Final **sigmoid** activation for binary classification.
- **Goal**: Correctly classify real vs. fake data.

### Objective Function (Minimax Game)

```
min_G max_D V(D, G) = E_x~p_data[log D(x)] + E_z~p_z[log(1 − D(G(z)))]
```

| Term | Meaning |
|------|---------|
| E[log D(x)] | D wants to maximize this → assign high probability to real data |
| E[log(1 − D(G(z)))] | D wants to maximize → assign low probability to fake data |
| G wants to minimize | G wants D(G(z)) → 1, making log(1 − D(G(z))) → −∞ |

### Training Algorithm

```
For each training iteration:
  1. Sample mini-batch of m noise vectors {z₁, ..., zₘ} ~ p_z(z)
  2. Sample mini-batch of m real examples {x₁, ..., xₘ} ~ p_data(x)
  
  # Train Discriminator (k steps, typically k=1):
  3. Generate fake samples: G(zᵢ) for each zᵢ
  4. Update D by ascending its stochastic gradient:
     ∇_θd [1/m Σ(log D(xᵢ) + log(1 − D(G(zᵢ))))]
  
  # Train Generator (1 step):
  5. Sample new noise vectors {z₁, ..., zₘ}
  6. Update G by descending its stochastic gradient:
     ∇_θg [1/m Σ log(1 − D(G(zᵢ)))]
     (In practice, maximize log D(G(z)) instead for stronger gradients)
```

### Working Principle — Adversarial Game

1. **G generates fake data** from random noise and tries to make it look real.
2. **D evaluates data** and tries to distinguish real from fake.
3. As D improves, G must produce better fakes to fool D.
4. As G improves, D must become more discerning.
5. **Nash Equilibrium**: Ideally, G produces perfect data (p_g = p_data) and D outputs 0.5 for all inputs (cannot distinguish).

### Convergence Properties

- At optimality, **p_g(x) = p_data(x)** — the generator's distribution matches the true data distribution.
- The optimal discriminator for a fixed G is: **D*(x) = p_data(x) / (p_data(x) + p_g(x))**.
- The global minimum of the minimax game is achieved when **D*(x) = 0.5** everywhere.

### Practical Considerations

- **Non-saturating loss** for G: Maximize log D(G(z)) instead of minimizing log(1 − D(G(z))) to avoid vanishing gradients early in training.
- **Training instability**: GANs are notoriously hard to train — requires careful hyperparameter tuning and architectural choices.
- Use **DCGAN guidelines**: batch norm, strided convolutions, Adam optimizer (lr=0.0002, β₁=0.5).

> GANs are powerful generative models that learn to produce realistic data through an adversarial game between a generator and discriminator, without explicitly modeling the data distribution.

//-----------------------------------------------------------------------------
// Includes
//-----------------------------------------------------------------------------
#include "MantidKernel/Math/Distributions/ChebyshevSeries.h"
#include <algorithm>
#include <cassert>

//-----------------------------------------------------------------------------
// Anonmouys static helpers
//-----------------------------------------------------------------------------

namespace Mantid {
namespace Kernel {

//-----------------------------------------------------------------------------
// Public members
//-----------------------------------------------------------------------------
/**
 * Constructor for an n-th order polynomial
 * @param n Order of the polynomial, which will require n+1 coefficients
 * to evaluate.
 */
ChebyshevSeries::ChebyshevSeries(const size_t n) : m_bk(n + 3, 0.0) {
  // The algorithm requires computing upto n+2 terms so space is
  // reserved for (n+1)+2 values.
}

/**
 * @param x X value to evaluate the polynomial in the range [-1,1]. No checking
 * is performed.
 * @param a_n Vector of (n+1) coefficients for the polynomial. They should be
 * ordered from 0->n. Providing more coefficients that required is not
 * considered an error.
 * @return Value of the polynomial. The value is undefined if x or n are
 * out of range
 */
double ChebyshevSeries::operator()(const std::vector<double> &a_n,
                                   const double x) {
  const size_t n = m_bk.size() - 3;
  assert(a_n.size() >= n + 1);
  // Start at top as each value of b_k requires the next 2 values
  m_bk.resize(n + 3);
  std::fill(m_bk.begin(), m_bk.end(), 0.0);
  for (size_t i = 0; i <= n; ++i) {
    size_t k = n - i;
    m_bk[k] = a_n[k] + 2. * x * m_bk[k + 1] - m_bk[k + 2];
  }
  return 0.5 * (m_bk[0] - m_bk[2]);
}

} // namespace Kernel
} // namespace Mantid

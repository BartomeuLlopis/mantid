#include "MantidMDAlgorithms/MDPlane.h"
#include "MantidKernel/System.h"
#include <stdexcept>

namespace Mantid
{
namespace MDAlgorithms
{

  //----------------------------------------------------------------------------------------------
  /** Constructor
   *
   * @param coeff :: vector of length nd of coefficients for the linear equation.
   * @param inequality :: RHS of the linear equation
   */
  MDPlane::MDPlane(const std::vector<coord_t> & coeff, const coord_t inequality)
  : m_inequality(inequality)
  {
    m_nd = coeff.size();
    if ((m_nd < 1) || (m_nd > 100)) throw std::invalid_argument("Invalid number of dimensions in the workspace!");
    m_coeff = new coord_t[m_nd];
    for (size_t d=0; d<m_nd; d++)
      m_coeff[d] = coeff[d];
  }

  //----------------------------------------------------------------------------------------------
  /** Constructor
   *
   * @param nd :: number of dimensions
   * @param coeff :: vector of length nd of coefficients for the linear equation.
   * @param inequality :: RHS of the linear equation
   */
  MDPlane::MDPlane(const size_t nd, const coord_t * coeff, const coord_t inequality)
  : m_nd(nd), m_inequality(inequality)
  {
    if ((m_nd < 1) || (m_nd > 100)) throw std::invalid_argument("Invalid number of dimensions in the workspace!");
    m_coeff = new coord_t[m_nd];
    for (size_t d=0; d<m_nd; d++)
      m_coeff[d] = coeff[d];
  }

    
  //----------------------------------------------------------------------------------------------
  /** Destructor
   */
  MDPlane::~MDPlane()
  {
    delete [] m_coeff;
  }
  
  //----------------------------------------------------------------------------------------------
  /** Is a point in MDimensions bounded by this hyperplane, that is,
   * is (a1*x1 + a2*x2 + ... < b)?
   *
   * @param coords :: nd-sized array of coordinates
   * @return true if it is bounded by the plane
   */
  bool MDPlane::isPointBounded(const coord_t * coords)
  {
    coord_t total = 0;
    for (size_t d=0; d<m_nd; d++)
    {
      total += m_coeff[d] * coords[d];
    }
    return (total < m_inequality);
  }



} // namespace Mantid
} // namespace MDAlgorithms


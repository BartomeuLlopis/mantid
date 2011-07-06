#include "GLActorCollection.h"
#include "OpenGLError.h"

#include "MantidKernel/Exception.h"

#include <stdexcept>
#include <iostream>
#include <functional>
#include <algorithm>
#include <float.h>

GLActorCollection::GLActorCollection()
  :GLActor(),
  m_minBound(DBL_MAX,DBL_MAX,DBL_MAX),
  m_maxBound(-DBL_MAX,-DBL_MAX,-DBL_MAX),
  m_displayListId(0),
  m_useDisplayList(false)
{
}

GLActorCollection::~GLActorCollection()
{
	for(std::vector<GLActor*>::iterator i=mActorsList.begin();i!=mActorsList.end();i++)
	{
	  delete (*i);
	}
	mActorsList.clear();
	if(m_displayListId != 0)
  {
		glDeleteLists(m_displayListId,1);
  }

}

/**
 * This method does the drawing by calling the list of actors to draw themselfs
 */
void GLActorCollection::draw(bool picking)const
{
  if (!isVisible()) return;
  OpenGLError::check("GLActorCollection::draw(0)");
  if (picking)
  {
    drawGL(picking);
  }
  else
  {
    if (m_useDisplayList)
    {
      glCallList(m_displayListId);
    }
    else if (m_displayListId == 0)
    {
      m_displayListId = glGenLists(1);
      // child actors can also create display lists, so delay
      // until all the children have finished making theirs
      drawGL(picking);
    }
    else
    {
      m_useDisplayList = true;
      glNewList(m_displayListId,GL_COMPILE); //Construct display list for object representation
      drawGL(picking);
      glEndList();
      if(glGetError()==GL_OUT_OF_MEMORY) //Throw an exception
        throw Mantid::Kernel::Exception::OpenGLError("OpenGL: Out of video memory");
      glCallList(m_displayListId);
    }
  }
  OpenGLError::check("GLActorCollection::draw()");
}

void GLActorCollection::drawGL(bool picking )const
{
  for(std::vector<GLActor*>::const_iterator it = mActorsList.begin();it != mActorsList.end();++it)
  {
    (**it).draw(picking);
  }
}

bool GLActorCollection::accept(const GLActorVisitor& visitor)
{
  const SetVisibilityVisitor* svv = dynamic_cast<const SetVisibilityVisitor*>(&visitor);
  // accepting a set visibility visitor. 
  if (svv)
  {
    if (visitor.visit(this)) return true;
    bool ok = false;
    for(std::vector<GLActor*>::const_iterator it = mActorsList.begin();it != mActorsList.end();++it)
    {
      if ((**it).accept(visitor))
      {
        ok = true;
      }
    }
    if (ok)
    {
      m_visible = true;
    }
    return ok;
  }

  // default visitor
  for(std::vector<GLActor*>::const_iterator it = mActorsList.begin();it != mActorsList.end();++it)
  {
    if ((**it).accept(visitor)) return true;
  }
  return visitor.visit(this);
}

/**
 * This method addes a new actor to the collection.
 * @param a :: input actor to be added to the list
 */
void GLActorCollection::addActor(GLActor* a)
{
  if( !a )
	{
	  return;
	}
	mActorsList.push_back(a);
  Mantid::Kernel::V3D minBound;
  Mantid::Kernel::V3D maxBound;
  a->getBoundingBox(minBound,maxBound);
  if(m_minBound[0]>minBound[0]) m_minBound[0]=minBound[0];
  if(m_minBound[1]>minBound[1]) m_minBound[1]=minBound[1];
  if(m_minBound[2]>minBound[2]) m_minBound[2]=minBound[2];
  if(m_maxBound[0]<maxBound[0]) m_maxBound[0]=maxBound[0];
  if(m_maxBound[1]<maxBound[1]) m_maxBound[1]=maxBound[1];
  if(m_maxBound[2]<maxBound[2]) m_maxBound[2]=maxBound[2];
}

/**
 * Remove the input actor from the collection
 * @param a :: input actor to be removed from the list
 */
void GLActorCollection::removeActor(GLActor*)
{
	throw std::runtime_error("Removing actor not implemented");
}

/**
 * This method returns the number of actors in the collection
 * @return integer value of number of actors in collection
 */
int  GLActorCollection::getNumberOfActors()
{
	return static_cast<int>(mActorsList.size());
}

/**
 * This method returns the actor at the given index
 * @param index :: is the index in actor collection to be returned
 * @return a pointer to the actor at a given index
 */
GLActor* GLActorCollection::getActor(int index)
{
	if(index<0||index> static_cast<int>(mActorsList.size()) )return NULL;
	return mActorsList.at(index);
}

void GLActorCollection::getBoundingBox(Mantid::Kernel::V3D& minBound,Mantid::Kernel::V3D& maxBound)const
{
  minBound = m_minBound;
  maxBound = m_maxBound;
}

void GLActorCollection::invalidateDisplayList()const
{
	if(m_displayListId != 0)
  {
		glDeleteLists(m_displayListId,1);
    m_displayListId = 0;
    m_useDisplayList = false;
  }
}

void GLActorCollection::setVisibility(bool on)
{
  for(std::vector<GLActor*>::const_iterator it = mActorsList.begin();it != mActorsList.end();++it)
  {
    (**it).setVisibility(on);
  }
}

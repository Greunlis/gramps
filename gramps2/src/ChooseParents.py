#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2003  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id$

"""
ChooseParents interface allows users to select the paretns of an
individual.
"""

__author__ = "Donald N. Allingham"
__version__ = "$Revision$"

#-------------------------------------------------------------------------
#
# internationalization
#
#-------------------------------------------------------------------------
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk.glade
import gnome

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import RelLib
import const
import Utils
import GrampsCfg
import ListModel

_titles = [(_('Name'),3,200),(_('ID'),1,50),(_('Birth date'),4,50),('',0,50),('',0,0)]

#-------------------------------------------------------------------------
#
# ChooseParents
#
#-------------------------------------------------------------------------
class ChooseParents:
    """
    Displays the Choose Parents dialog box, allowing the parents
    to be edited.
    """
    def __init__(self,db,person,family,family_update,full_update):
        """
        Creates a ChoosePerson dialog box.

        db - database associated the person
        person - person whose parents we are selecting
        family - current family
        family_update - task that updates the family display
        full_update - task that updates the main display 
        """
        self.db = db
        self.person = person
        self.family = family
        self.family_update = family_update
        self.full_update = full_update
        self.old_type = ""
        self.type = ""
        self.parent_selected = 0

        self.date = person.get_birth().get_date_object()

        if self.family:
            self.father = self.family.get_father_id()
            self.mother = self.family.get_mother_id()
        else:
            self.mother = None
            self.father = None

        self.glade = gtk.glade.XML(const.gladeFile,"familyDialog","gramps")
        self.top = self.glade.get_widget("familyDialog")

        text = _("Choose the Parents of %s") % GrampsCfg.nameof(self.person)
        Utils.set_titles(self.top,self.glade.get_widget('title'),
                         text,_('Choose Parents'))
        
	self.mother_rel = self.glade.get_widget("mrel")
	self.father_rel = self.glade.get_widget("frel")
        self.fcombo = self.glade.get_widget("prel_combo")
        self.prel = self.glade.get_widget("prel")
        self.title = self.glade.get_widget("chooseTitle")
        self.father_list = self.glade.get_widget("father_list")
        self.mother_list = self.glade.get_widget("mother_list")
        self.flabel = self.glade.get_widget("flabel")
        self.mlabel = self.glade.get_widget("mlabel")
        self.showallf = self.glade.get_widget('showallf')
        self.showallm = self.glade.get_widget('showallm')
        
        self.fcombo.set_popdown_strings(const.familyRelations)

        self.fmodel = ListModel.ListModel(self.father_list, _titles,
                                          self.father_list_select_row)
        self.mmodel = ListModel.ListModel(self.mother_list, _titles,
                                          self.mother_list_select_row)

        for (f,mr,fr) in self.person.get_parent_family_id_list():
            if f == self.family:
                self.mother_rel.set_text(_(mr))
                self.father_rel.set_text(_(fr))
                break
        else:
            self.mother_rel.set_text(_("Birth"))
            self.father_rel.set_text(_("Birth"))

        if self.family:
            self.type = self.family.get_relationship()
        else:
            self.type = "Married"

        self.prel.set_text(_(self.type))
        self.redrawf()
        self.redrawm()
        
        self.glade.signal_autoconnect({
            "on_save_parents_clicked"  : self.save_parents_clicked,
            "on_add_parent_clicked"    : self.add_parent_clicked,
            "on_prel_changed"          : self.parent_relation_changed,
            "on_showallf_toggled"      : self.showallf_toggled,
            "on_showallm_toggled"      : self.showallm_toggled,
            "destroy_passed_object"    : Utils.destroy_passed_object,
            "on_help_familyDialog_clicked"  : self.on_help_clicked,
            })

    def on_help_clicked(self,obj):
        """Display the relevant portion of GRAMPS manual"""
        gnome.help_display('gramps-manual','gramps-edit-quick')
        self.val = self.top.run()

    def redrawf(self):
        """Redraws the potential father list"""

        self.fmodel.clear()
        self.fmodel.new_model()

        pkey = self.person.get_id()

        if self.father:
            fid = self.father.get_id()
        else:
            fid = None
            
        bday = self.person.get_birth().get_date_object()
        dday = self.person.get_death().get_date_object()

        person_list = []
        for key in self.db.sort_person_keys():
            if pkey == key:
                continue

            person = self.db.get_person(key)
            if person.get_gender() != person.male:
                continue

            if not self.showallf.get_active():
                
                pdday = person.get_death().get_date_object()
                pbday = person.get_birth().get_date_object()

        	if bday.getYearValid():
                    if pbday.getYearValid():
                        # reject if parents birthdate + 10 > child birthdate
                        if pbday.getLowYear()+10 > bday.getHighYear():
                            continue

                        # reject if parents birthdate + 90 < child birthdate 
                        if pbday.getHighYear()+90 < bday.getLowYear():
                            continue

                    if pdday.getYearValid():
                        # reject if parents birthdate + 10 > child deathdate 
                        if pbday.getLowYear()+10 > dday.getHighYear():
                            continue
                
                if dday.getYearValid():
                    if pbday.getYearValid():
                        # reject if parents deathday + 3 < childs birth date 
                        if pdday.getHighYear()+3 < bday.getLowYear():
                            continue

                    if pdday.getYearValid():
                        # reject if parents deathday + 150 < childs death date 
                        if pdday.getHighYear() + 150 < dday.getLowYear():
                            continue
        
            person_list.append(person.get_id())

	for idval in person_list:
            d = self.db.get_person_display(idval)
            info = [d[0],d[1],d[3],d[5],d[6]]
            if self.type == "Partners":
                self.fmodel.add(info,d[1],fid==d[1])
            elif d[2] == const.male:
                self.fmodel.add(info,d[1],fid==d[1])

        if self.type == "Partners":
            self.flabel.set_label("<b>%s</b>" % _("Par_ent"))
        else:
            self.flabel.set_label("<b>%s</b>" % _("Fath_er"))

        self.fmodel.connect_model()


    def redrawm(self):
        """Redraws the potential mother list"""

        self.mmodel.clear()
        self.mmodel.new_model()

        pkey = self.person.get_id()

        if self.mother:
            mid = self.mother.get_id()
        else:
            mid = None
            
        bday = self.person.get_birth().get_date_object()
        dday = self.person.get_death().get_date_object()

        person_list = []
        for key in self.db.sort_person_keys():
            if pkey == key:
                continue

            person = self.db.get_person(key)
            if person.get_gender() != person.female:
                continue

            person = self.db.get_person(key)

            if not self.showallm.get_active():
                
                pdday = person.get_death().get_date_object()
                pbday = person.get_birth().get_date_object()

        	if bday.getYearValid():
                    if pbday.getYearValid():
                        # reject if parents birthdate + 10 > child birthdate
                        if pbday.getLowYear()+10 > bday.getHighYear():
                            continue

                        # reject if parents birthdate + 90 < child birthdate 
                        if pbday.getHighYear()+90 < bday.getLowYear():
                            continue

                    if pdday.getYearValid():
                        # reject if parents birthdate + 10 > child deathdate 
                        if pbday.getLowYear()+10 > dday.getHighYear():
                            continue
                
                if dday.getYearValid():
                    if pbday.getYearValid():
                        # reject if parents deathday + 3 < childs birth date 
                        if pdday.getHighYear()+3 < bday.getLowYear():
                            continue

                    if pdday.getYearValid():
                        # reject if parents deathday + 150 < childs death date 
                        if pdday.getHighYear() + 150 < dday.getLowYear():
                            continue
        
            person_list.append(person.get_id())

	for idval in person_list:
            d = self.db.get_person_display(idval)
            info = [d[0],d[1],d[3],d[5],d[6]]
            if self.type == "Partners":
                self.mmodel.add(info,d[1],mid==d[1])
            elif d[2] == const.female:
                self.mmodel.add(info,d[1],mid==d[1])

        if self.type == "Partners":
            self.mlabel.set_label("<b>%s</b>" % _("Pa_rent"))
        else:
            self.mlabel.set_label("<b>%s</b>" % _("Mothe_r"))
        self.mmodel.connect_model()

    def parent_relation_changed(self,obj):
        """Called everytime the parent relationship information is changegd"""
        self.old_type = self.type
        self.type = const.save_frel(unicode(obj.get_text()))
        if self.old_type == "Partners" or self.type == "Partners":
            self.redrawf()
            self.redrawm()

    def showallf_toggled(self,obj):
        self.redrawf()

    def showallm_toggled(self,obj):
        self.redrawm()
        
    def find_family(self,father,mother):
        """
        Finds the family associated with the father and mother.
        If one does not exist, it is created.
        """
        if not father and not mother:
            return None
	
        families = self.db.get_family_id_map().values()
        for family in families:
            if family.get_father_id() == father and family.get_mother_id() == mother:
                return family
            elif family.get_father_id() == mother and family.get_mother_id() == father:
                return family

        family = self.db.new_family()
        family.set_father_id(father)
        family.set_mother_id(mother)
        family.add_child_id(self.person)
    
        if father:
            father.add_family_id(family.get_id())
        if mother:
            mother.add_family_id(family.get_id())
        return family

    def mother_list_select_row(self,obj):
        """Called when a row is selected in the mother list. Sets the
        active mother based off the id associated with the row."""
        
        model, iter = self.mmodel.get_selected()
        if iter:
            id = model.get_value(iter,1)
            self.mother = self.db.get_person(id)
        else:
            self.mother = None

        if not self.parent_selected and self.mother:
            self.parent_selected = 1
            list = self.mother.get_family_id_list()
            if len(list) >= 1:
                father = list[0].get_father_id()
                self.fmodel.find(father.get_id())
                self.fmodel.center_selected()

    def father_list_select_row(self,obj):
        """Called when a row is selected in the father list. Sets the
        active father based off the id associated with the row."""
        model, iter = self.fmodel.get_selected()
        if iter:
            id = model.get_value(iter,1)
            self.father = self.db.get_person(id)
        else:
            self.father = None

        if not self.parent_selected and self.father:
            self.parent_selected = 1
            list = self.father.get_family_id_list()
            if len(list) >= 1:
                mother = list[0].get_mother_id()
                self.mmodel.find(mother.get_id())
                self.mmodel.center_selected()

    def save_parents_clicked(self,obj):
        """
        Called with the OK button nis pressed. Saves the selected people as parents
        of the main perosn.
        """
        try:
            mother_rel = const.child_relations(self.mother_rel.get_text())
        except KeyError:
            mother_rel = const.child_relations("Birth")

        try:
            father_rel = const.child_relations(self.father_rel.get_text())
        except KeyError:
            father_rel = const.childRelations("Birth")

        if self.father or self.mother:
            if self.mother and not self.father:
                if self.mother.get_gender() == RelLib.Person.male:
                    self.father = self.mother
                    self.mother = None
                self.family = self.find_family(self.father,self.mother)
            elif self.father and not self.mother: 
                if self.father.get_gender() == RelLib.Person.female:
                    self.mother = self.father
                    self.father = None
                self.family = self.find_family(self.father,self.mother)
            elif self.mother.get_gender() != self.father.get_gender():
                if self.type == "Partners":
                    self.type = "Unknown"
                if self.father.get_gender() == RelLib.Person.female:
                    x = self.father
                    self.father = self.mother
                    self.mother = x
                self.family = self.find_family(self.father,self.mother)
            else:
                self.type = "Partners"
                self.family = self.find_family(self.father,self.mother)
        else:    
            self.family = None

        Utils.destroy_passed_object(obj)
        if self.family:
            self.family.set_relationship(self.type)
            self.change_family_type(self.family,mother_rel,father_rel)
        self.family_update(None)

    def add_new_parent(self,epo):
        """Adds a new person to either the father list or the mother list,
        depending on the gender of the person."""

        person = epo.person
        id = person.get_id()

        if id == "":
            id = self.db.add_person(person)
        else:
            self.db.add_person_no_map(person,id)
        self.db.build_person_display(id)

        self.type = const.save_frel(unicode(self.prel.get_text()))
        dinfo = self.db.get_person_display(id)
        rdata = [dinfo[0],dinfo[1],dinfo[3],dinfo[5],dinfo[6]]

        if self.type == "Partners":
            self.parent_relation_changed(self.prel)
        elif person.get_gender() == RelLib.Person.male:
            self.fmodel.add(rdata,None,1)
            self.fmodel.center_selected()
        else:
            self.mmodel.add(rdata,None,1)
            self.mmodel.center_selected()
        self.full_update()
        
    def add_parent_clicked(self,obj):
        """Called with the Add New Person button is pressed. Calls the QuickAdd
        class to create a new person."""
        
        person = RelLib.Person()
        person.set_gender(RelLib.Person.male)
        
        try:
            import EditPerson
            EditPerson.EditPerson(person,self.db,self.add_new_parent)
        except:
            import DisplayTrace
            DisplayTrace.DisplayTrace()

    def change_family_type(self,family,mother_rel,father_rel):
        """
        Changes the family type of the specified family. If the family
        is None, the the relationship type shoud be deleted.
        """
        if self.person not in family.get_child_id_list():
            family.add_child_id(self.person)
        for fam in self.person.get_parent_family_id_list():
            if family == fam[0]:
                if mother_rel == fam[1] and father_rel == fam[2]:
                    return
                if mother_rel != fam[1] or father_rel != fam[2]:
                    self.person.remove_parent_family_id(family.get_id())
                    self.person.add_parent_family_id(family.get_id(),mother_rel,father_rel)
                    break
        else:
            self.person.add_parent_family_id(family.get_id(),mother_rel,father_rel)
        Utils.modified()


class ModifyParents:
    def __init__(self,db,person,family,family_update,full_update,parent_window=None):
        """
        Creates a ChoosePerson dialog box.

        db - database associated the person
        person - person whose parents we are selecting
        family - current family
        family_update - task that updates the family display
        full_update - task that updates the main display 
        """
        self.db = db
        self.person = person
        self.family = family
        self.family_update = family_update
        self.full_update = full_update
        
        self.father = self.family.get_father_id()
        self.mother = self.family.get_mother_id()

        self.glade = gtk.glade.XML(const.gladeFile,"modparents","gramps")
        self.top = self.glade.get_widget("modparents")
        self.title = self.glade.get_widget("title")

        title = _("Modify the Parents of %s") % GrampsCfg.nameof(self.person)
        Utils.set_titles(self.top, self.title, title, _("Modify Parents"))
        
	self.mother_rel = self.glade.get_widget("mrel")
	self.father_rel = self.glade.get_widget("frel")
        self.flabel = self.glade.get_widget("flabel")
        self.mlabel = self.glade.get_widget("mlabel")

        self.orig_mrel = _("Birth")
        self.orig_frel = _("Birth")
        for (f,mr,fr) in self.person.get_parent_family_id_list():
            if f == self.family:
                self.orig_mrel = _(mr)
                self.orig_frel = _(fr)

        self.mother_rel.set_text(self.orig_mrel)
        self.father_rel.set_text(self.orig_frel)

        self.glade.signal_autoconnect({
            "on_parents_help_clicked"  : self.on_help_clicked,
            })

        self.title.set_use_markup(gtk.TRUE)

        if self.family.get_relationship() == "Partners":
            self.mlabel.set_label('<b>%s</b>' % _("Parent"))
            self.flabel.set_label('<b>%s</b>' % _("Parent"))
        else:
            self.mlabel.set_label('<b>%s</b>' % _("Mother"))
            self.flabel.set_label('<b>%s</b>' % _("Father"))


        if self.father:
            fname = self.father.get_primary_name().get_name()
            self.glade.get_widget("fname").set_text(fname)
        else:
            self.father_rel.set_sensitive(0)
            
        if self.mother:
            mname = self.mother.get_primary_name().get_name()
            self.glade.get_widget("mname").set_text(mname)
        else:
            self.mother_rel.set_sensitive(0)

        self.pref = self.glade.get_widget('preferred')
        if len(self.person.get_parent_family_id_list()) > 1:
            self.glade.get_widget('pref_label').show()
            self.pref.show()
            if family == self.person.get_parent_family_id_list()[0]:
                self.pref.set_active(1)
            else:
                self.pref.set_active(0)

        if parent_window:
            self.top.set_transient_for(parent_window)
        self.val = self.top.run()
        if self.val == gtk.RESPONSE_OK:
            self.save_parents_clicked()
        self.top.destroy()


    def on_help_clicked(self,obj):
        """Display the relevant portion of GRAMPS manual"""
        gnome.help_display('gramps-manual','gramps-spec-par')
        self.val = self.top.run()

    def save_parents_clicked(self):
        """
        Called with the OK button nis pressed. Saves the selected people as parents
        of the main perosn.
        """
        mother_rel = const.childRelations(self.mother_rel.get_text())
        father_rel = const.childRelations(self.father_rel.get_text())
        mod = 0

        if mother_rel != self.orig_mrel or father_rel != self.orig_frel:
            self.person.remove_parent_family_id(self.family)
            self.person.add_parent_family_id(self.family,mother_rel,father_rel)
            mod = 1
            Utils.modified()

        if len(self.person.get_parent_family_id_list()):
            make_pref = self.pref.get_active()

            plist = self.person.get_parent_family_id_list()
            if make_pref:
                if self.family != plist[0]:
                    self.person.set_main_parent_family_id(self.family)
                    Utils.modified()
                    mod = 1
            else:
                if self.family == plist[0]:
                    self.person.set_main_parent_family_id(plist[0])
                    Utils.modified()
                    mod = 1

        if mod:
            self.family_update(None)

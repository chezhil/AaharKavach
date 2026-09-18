// Admin can perform any action on any profile within their household
permit (
    principal,
    action in [
        AaharKavach::Action::"ReadProfile",
        AaharKavach::Action::"CreateProfile",
        AaharKavach::Action::"UpdateProfile",
        AaharKavach::Action::"DeleteProfile"
    ],
    resource
)
when { principal.role == "Admin" && principal.householdId == resource.householdId };

// Member can read any profile in their household
permit (
    principal,
    action == AaharKavach::Action::"ReadProfile",
    resource
)
when { (principal.role == "Member" || principal.role == "Child") && principal.householdId == resource.householdId };

// Member can only update their own profile
permit (
    principal,
    action == AaharKavach::Action::"UpdateProfile",
    resource
)
when { principal.role == "Member" && principal == resource.owner };

namespace AaharKavach {
    entity User {
        role: String,
        householdId: String
    };

    entity Profile {
        owner: User,
        householdId: String
    };

    action "ReadProfile", "CreateProfile", "UpdateProfile", "DeleteProfile";
}
